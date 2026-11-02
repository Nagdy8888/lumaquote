"""Load and validate the frozen-evaluation scenario set and its evaluator-only answer key.

The scenarios (`scenarios.json`) are the only inputs a system under test may see.
The oracle (`oracle.json`) holds expected actions and is read only by evaluators.
This module is development tooling: no application, prompt, catalog ingestion or
trace code may import it or read either file (enforced by a unit test).
"""

import hashlib
import json
import re
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/evaluation"
SCENARIO_FILE = FIXTURES / "scenarios.json"
ORACLE_FILE = FIXTURES / "oracle.json"

MODALITY_TOTALS = {"text": 40, "voice": 24, "photo": 16}
SPLIT_TOTALS = {"development": 60, "holdout": 20}
ACTIONS = {"draft_quote", "needs_staff", "clarify"}
REASONS = {
    "complete_written_order",
    "needs_written_confirmation",
    "prose_not_exact_order",
    "unit_or_quantity_not_explicit",
    "incomplete_correction",
    "cancellation_or_negation",
    "alternatives_or_conditions",
    "invalid_sku_format",
    "no_product_specified",
    "no_matching_product",
    "descriptive_candidates",
    "injected_authority",
    "stock_insufficient",
    "out_of_stock",
    "discontinued",
    "unknown_sku",
}
TURN_KIND = {"text": "text", "voice": "audio", "photo": "image"}
CENT = Decimal("0.01")
SKU = re.compile(r"[A-Z]{2}-\d{3}")

# Independent restatement of the synthetic catalog (`luma.setup.bootstrap`): six
# families of twelve models. Model n (1-based) has index i=n-1; CCT cycles
# 3000/4000/5000 by i%3, power steps +3 W and price +8 USD every three models,
# model 11 is out of stock, model 12 is discontinued. A unit test compares the
# family table to the bootstrap source so silent drift is detected.
FAMILIES = {
    "DL": ("Downlights", 18, 32, "IP44"),
    "LN": ("Linear systems", 36, 79, "IP44"),
    "TR": ("Track lighting", 25, 58, "IP44"),
    "HB": ("High bays", 120, 145, "IP65"),
    "OD": ("Outdoor lighting", 50, 94, "IP65"),
    "EM": ("Emergency lighting", 8, 48, "IP44"),
}


def catalog_model() -> dict[str, dict]:
    """Return the expected synthetic catalog keyed by SKU, derived without database or application code."""
    catalog = {}
    for prefix, (_, watts, base_price, ip) in FAMILIES.items():
        for i in range(12):
            catalog[f"{prefix}-{i + 1:03d}"] = {
                "price": Decimal(base_price + (i // 3) * 8),
                "watts": watts + (i // 3) * 3,
                "cct": [3000, 4000, 5000][i % 3],
                "ip": ip,
                "available": 0 if i == 10 else 180 - i * 9,
                "discontinued": i == 11,
            }
    return catalog


def load() -> tuple[list[dict], dict[str, dict]]:
    """Read both fixture files; raises FileNotFoundError or ValueError when missing or malformed."""
    scenarios = json.loads(SCENARIO_FILE.read_text(encoding="utf-8"))
    oracle = json.loads(ORACLE_FILE.read_text(encoding="utf-8"))
    if scenarios.get("version") != 1 or oracle.get("version") != 1:
        raise ValueError("Unsupported evaluation fixture version.")
    return scenarios["scenarios"], oracle["oracle"]


def fingerprints() -> dict[str, str]:
    """Return SHA-256 digests of the exact fixture bytes, for evidence and the future freeze record."""
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (SCENARIO_FILE, ORACLE_FILE)}


def denominators(scenarios: list[dict]) -> dict[str, dict[str, int]]:
    """Count scenarios by split and modality; reports must always show these denominators."""
    counts = Counter((item["split"], item["modality"]) for item in scenarios)
    return {
        split: {modality: counts[(split, modality)] for modality in MODALITY_TOTALS} for split in SPLIT_TOTALS
    }


def supported(catalog: dict, sku: str, quantity: int) -> str | None:
    """Return None when a line can be quoted from observed stock, else the oracle reason it cannot."""
    product = catalog.get(sku)
    if product is None:
        return "unknown_sku"
    if product["discontinued"]:
        return "discontinued"
    if product["available"] == 0:
        return "out_of_stock"
    if quantity > product["available"]:
        return "stock_insufficient"
    return None


def subtotal(catalog: dict, lines: list[dict]) -> str:
    """Compute the canonical USD subtotal (tax excluded, no discount or shipping) from catalog prices."""
    total = sum((catalog[line["sku"]]["price"] * line["quantity"] for line in lines), Decimal(0))
    return str(total.quantize(CENT, rounding=ROUND_HALF_UP))


def score(
    item: dict, entry: dict, observed: list[str], subtotal: str | None, replies: list[str] | None = None
) -> dict:
    """Compare one run's per-turn actions, final subtotal and reply text with the answer key.

    `replies` are the customer-visible reply texts in order; they are scanned for
    catalog codes to judge labeled retrieval (target within the offered candidates).
    A scenario passes when every checkpoint action is the expected one or a listed
    `also_acceptable` safe alternative (staff escalation for media whose declared
    conditions make the reading unreliable) and a drafted subtotal equals the
    independently computed one. `exact_match` records whether only primary actions
    were observed, so the strict and the safe-equivalent rate are both reportable. Other fields feed the plan's
    targets: acting on ambiguity, unsupported final lines and retrieval recall.
    """
    expected = [checkpoint["action"] for checkpoint in entry["checkpoints"]]
    allowed = [
        [checkpoint["action"], *checkpoint.get("also_acceptable", [])] for checkpoint in entry["checkpoints"]
    ]
    exact = observed == expected and subtotal == entry["expected_subtotal"]
    acceptable = (
        len(observed) == len(allowed)
        and all(got in options for got, options in zip(observed, allowed, strict=True))
        and subtotal == entry["expected_subtotal"]
    )
    passed = acceptable
    recall = None
    if entry["retrieval"]:
        offered = {code for text in replies or [] for code in SKU.findall(text.upper())}
        recall = any(target in offered for target in entry["retrieval"]["target_skus"])
    return {
        "id": item["id"],
        "modality": item["modality"],
        "status": "passed" if passed else "failed",
        "exact_match": exact,
        "expected_actions": expected,
        "observed_actions": observed,
        "expected_subtotal": entry["expected_subtotal"],
        "observed_subtotal": subtotal,
        "first_turn_acts_on_ambiguity": observed[0] != "draft_quote"
        if entry["consequential_ambiguity"]
        else None,
        "unsupported_final_line": bool(observed)
        and observed[-1] == "draft_quote"
        and expected[-1] != "draft_quote",
        "retrieval_recall_at_5": recall,
    }


def _check_structure(scenarios: list[dict], oracle: dict) -> list[str]:
    """Check counts, identity, the family-level split and that scenarios carry no answers."""
    errors = []
    ids = [item["id"] for item in scenarios]
    if len(set(ids)) != len(ids):
        errors.append("scenario ids are not unique")
    if set(ids) != set(oracle):
        errors.append("scenario ids and oracle ids differ")
    for item in scenarios:
        if set(item) != {"id", "family", "modality", "split", "turns"}:
            errors.append(f"{item.get('id')}: scenario fields must be exactly id/family/modality/split/turns")
    totals = Counter(item["modality"] for item in scenarios)
    if dict(totals) != MODALITY_TOTALS:
        errors.append(f"modality totals {dict(totals)} differ from {MODALITY_TOTALS}")
    splits = Counter(item["split"] for item in scenarios)
    if dict(splits) != SPLIT_TOTALS:
        errors.append(f"split totals {dict(splits)} differ from {SPLIT_TOTALS}")
    family_splits: dict[str, set] = {}
    for item in scenarios:
        family_splits.setdefault(item["family"], set()).add(item["split"])
    for family, seen in family_splits.items():
        if len(seen) > 1:
            errors.append(f"family {family} crosses the development/holdout boundary")
    return errors


def _check_turns(item: dict, entry: dict) -> list[str]:
    """Check one scenario's turns against its checkpoints and the media-cannot-confirm rule."""
    sid, errors = item["id"], []
    turns, checkpoints = item["turns"], entry["checkpoints"]
    if not turns or turns[0]["kind"] != TURN_KIND[item["modality"]]:
        errors.append(f"{sid}: first turn must be {TURN_KIND[item['modality']]}")
    if [c["after_turn"] for c in checkpoints] != list(range(len(turns))):
        errors.append(f"{sid}: exactly one checkpoint per customer turn is required")
        return errors
    for turn, checkpoint in zip(turns, checkpoints, strict=True):
        if checkpoint["action"] not in ACTIONS or checkpoint["reason"] not in REASONS:
            errors.append(f"{sid}: unknown action or reason {checkpoint}")
        if turn["kind"] in ("audio", "image"):
            spec = turn["spec"]
            if spec.get("asset") is not None and not (FIXTURES / spec["asset"]).is_file():
                errors.append(f"{sid}: declared media asset is missing")
            if (checkpoint["action"], checkpoint["reason"]) != ("clarify", "needs_written_confirmation"):
                errors.append(f"{sid}: media must stay at clarification until a written confirmation")
            if checkpoint.get("also_acceptable", []) not in ([], ["needs_staff"]):
                errors.append(f"{sid}: media may additionally allow only staff escalation")
        elif checkpoint.get("also_acceptable"):
            errors.append(f"{sid}: only unreliable media checkpoints may list alternatives")
        elif turn["kind"] != "text" or not turn["text"].strip():
            errors.append(f"{sid}: malformed text turn")
    return errors


def _check_outcome(item: dict, entry: dict, catalog: dict) -> list[str]:
    """Independently verify the expected workflow outcome, lines and subtotal against catalog facts."""
    sid, errors = item["id"], []
    final = entry["checkpoints"][-1]["action"]
    lines = entry["requested_lines"]
    if final == "clarify":
        if lines or entry["expected_subtotal"] is not None:
            errors.append(f"{sid}: a clarification must not carry order lines or a subtotal")
        return errors
    if not lines:
        errors.append(f"{sid}: {final} requires requested lines")
        return errors
    last = item["turns"][-1]
    if last["kind"] != "text":
        errors.append(f"{sid}: a final order must be a written text turn")
    for line in lines:
        text = last.get("text", "")
        if not SKU.fullmatch(line["sku"]) or type(line["quantity"]) is not int or line["quantity"] < 1:
            errors.append(f"{sid}: malformed line {line}")
        elif line["sku"] not in text.upper() or not re.search(rf"\b{line['quantity']}\b", text):
            errors.append(f"{sid}: line {line} is not stated in the final written turn")
    if len({line["sku"] for line in lines}) != len(lines):
        errors.append(f"{sid}: duplicate SKU lines")
    problems = [supported(catalog, line["sku"], line["quantity"]) for line in lines]
    if final == "draft_quote":
        if any(problems):
            errors.append(f"{sid}: draft_quote lines are not all supported: {problems}")
        elif entry["expected_subtotal"] != subtotal(catalog, lines):
            errors.append(f"{sid}: subtotal {entry['expected_subtotal']} != {subtotal(catalog, lines)}")
    elif not any(problems):
        errors.append(f"{sid}: needs_staff requires an unsupported line")
    elif entry["checkpoints"][-1]["reason"] not in {p for p in problems if p}:
        errors.append(f"{sid}: needs_staff reason does not match an unsupported line")
    if final == "needs_staff" and entry["expected_subtotal"] is not None:
        errors.append(f"{sid}: needs_staff must not carry a subtotal")
    return errors


def _check_retrieval(item: dict, entry: dict, catalog: dict) -> list[str]:
    """Check that labeled retrieval targets are current catalog models matching the stated specification."""
    target = entry["retrieval"]
    if target is None:
        return []
    errors = []
    for sku in target["target_skus"]:
        product = catalog.get(sku)
        if product is None or product["discontinued"]:
            errors.append(f"{item['id']}: retrieval target {sku} is not a current model")
    return errors


def validate(scenarios: list[dict], oracle: dict) -> list[str]:
    """Return every structural or consistency problem found; an empty list means the dataset is coherent.

    Passing proves only internal consistency with the catalog model, the 40/24/16
    and 60/20 counts and the family-level split. It says nothing about system
    quality and does not run a model, audio or image.
    """
    errors = _check_structure(scenarios, oracle)
    if errors:
        return errors
    catalog = catalog_model()
    for item in scenarios:
        entry = oracle[item["id"]]
        problems = _check_turns(item, entry)
        if not problems:
            problems = _check_outcome(item, entry, catalog) + _check_retrieval(item, entry, catalog)
        errors += problems
    return errors


FREEZE_FILE = FIXTURES / "freeze.json"
FROZEN_GLOBS = (
    "app/agents/luma_agent/**/*.py",
    "app/backend/luma/features/catalog/*.py",
    "app/backend/luma/features/media/*.py",
    "app/backend/luma/features/quotations/drafting.py",
    "app/backend/luma/features/quotations/rules.py",
)
FROZEN_FIXTURES = ("scenarios.json", "oracle.json", "media/MANIFEST.json")


def freeze_fingerprints() -> dict:
    """Hash everything a holdout result depends on: fixtures, agent/retrieval code and model configuration.

    The code set is the agent runtime, catalog retrieval, media handling and the deterministic
    drafting rules, so any prompt, node, threshold or parser change alters it. Model names and the
    allowance come from settings because a different model is a different system under test.
    """
    from luma.core.config import settings

    config = settings()
    code = {}
    for pattern in FROZEN_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if "__pycache__" not in path.parts:
                code[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "fixtures": {
            name: hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() for name in FROZEN_FIXTURES
        },
        "code": code,
        "model_configuration": {
            "openai_model": config.openai_model,
            "transcription_model": config.transcription_model,
            "embedding_model": config.embedding_model,
            "reservation": config.reservation,
        },
    }


def load_freeze() -> dict | None:
    """Return the committed freeze record, or None when the holdout has not been frozen."""
    return json.loads(FREEZE_FILE.read_text(encoding="utf-8")) if FREEZE_FILE.is_file() else None


def freeze_problems(record: dict | None, current: dict) -> list[str]:
    """List why a holdout run is not allowed: missing freeze, drifted fixtures/code/config, or a spent holdout.

    The holdout is one-shot. Any recorded run means its result may have influenced later changes,
    so a new claim needs new reserved cases (docs/TESTING_PLAN.md section 9), never a rerun.
    """
    if record is None:
        return ["no freeze record exists"]
    problems = []
    for section in ("fixtures", "code", "model_configuration"):
        if record.get(section) != current[section]:
            changed = sorted(
                key
                for key in set(record.get(section, {})) | set(current[section])
                if record.get(section, {}).get(key) != current[section].get(key)
            )
            problems.append(f"{section} changed since the freeze: {', '.join(changed[:6]) or 'structure'}")
    if record.get("holdout_runs"):
        problems.append("the holdout was already consumed by a recorded run")
    return problems
