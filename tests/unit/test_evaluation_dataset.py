"""The 80-scenario evaluation set is coherent, correctly split and kept away from runtime code."""

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import evaluation_dataset as dataset  # noqa: E402
from luma.setup.bootstrap import FAMILIES as BOOTSTRAP_FAMILIES  # noqa: E402


@pytest.fixture
def loaded():
    """Return independent deep copies so a mutation test cannot affect another test."""
    scenarios, oracle = dataset.load()
    return copy.deepcopy(scenarios), copy.deepcopy(oracle)


def test_shipped_dataset_is_valid():
    """The committed fixtures satisfy every structural and catalog-consistency rule."""
    scenarios, oracle = dataset.load()
    assert dataset.validate(scenarios, oracle) == []


def test_counts_and_family_split_match_the_plan():
    """40/24/16 modalities, 60/20 split and no family on both sides of the holdout boundary."""
    scenarios, _ = dataset.load()
    assert len(scenarios) == 80
    assert dataset.denominators(scenarios) == {
        "development": {"text": 30, "voice": 18, "photo": 12},
        "holdout": {"text": 10, "voice": 6, "photo": 4},
    }
    families = {}
    for item in scenarios:
        families.setdefault(item["family"], set()).add(item["split"])
    assert len(families) == 20 and all(len(splits) == 1 for splits in families.values())


def test_family_table_matches_the_bootstrap_catalog():
    """The independent catalog restatement cannot silently drift from the seeded synthetic catalog."""
    expected = {prefix: (family, watts, base) for family, prefix, _, watts, _, base in BOOTSTRAP_FAMILIES}
    restated = {prefix: (value[0], value[1], value[2]) for prefix, value in dataset.FAMILIES.items()}
    assert restated == expected


def test_scenarios_never_contain_answers(loaded):
    """Inputs expose no expected action, reason, line, subtotal or retrieval target."""
    scenarios, _ = loaded
    text = str(scenarios)
    for forbidden in ("checkpoints", "expected_subtotal", "target_skus", "requested_lines", "needs_staff"):
        assert forbidden not in text


def test_runtime_code_never_reads_the_answer_key():
    """Application, GAS and migration sources do not mention the evaluation fixtures or this module."""
    for folder in ("app", "gas", "supabase"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".gs", ".sql", ".json"}:
                content = path.read_text(encoding="utf-8", errors="ignore")
                assert "fixtures/evaluation" not in content and "evaluation_dataset" not in content, path


def test_every_media_turn_has_a_hashed_asset_and_stays_unconfirmed(loaded):
    """Each of the 40 media turns links an existing synthetic file whose bytes match the manifest and never confirms a field."""
    scenarios, oracle = loaded
    manifest = json.loads((dataset.FIXTURES / "media/MANIFEST.json").read_text(encoding="utf-8"))
    media_turns = 0
    for item in scenarios:
        for turn, checkpoint in zip(item["turns"], oracle[item["id"]]["checkpoints"], strict=True):
            if turn["kind"] != "text":
                media_turns += 1
                path = dataset.FIXTURES / turn["spec"]["asset"]
                assert path.is_file()
                assert manifest[path.name]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
                assert checkpoint["reason"] == "needs_written_confirmation"
    assert media_turns == 40 == len(manifest)


def test_media_manifest_never_records_outcomes():
    """The manifest lists generation facts only, so filenames and metadata cannot leak the answer key."""
    text = (dataset.FIXTURES / "media/MANIFEST.json").read_text(encoding="utf-8")
    for forbidden in ("draft_quote", "needs_staff", "clarify", "expected", "subtotal"):
        assert forbidden not in text


def test_validator_rejects_a_wrong_subtotal(loaded):
    """The independent catalog arithmetic catches a mistyped expected total."""
    scenarios, oracle = loaded
    sid = next(k for k, v in oracle.items() if v["expected_subtotal"])
    oracle[sid]["expected_subtotal"] = "0.01"
    assert any("subtotal" in error for error in dataset.validate(scenarios, oracle))


def test_validator_rejects_a_quote_for_unsupported_stock(loaded):
    """A draft_quote oracle for a discontinued or out-of-stock line is an authoring error."""
    scenarios, oracle = loaded
    sid = next(k for k, v in oracle.items() if v["expected_subtotal"])
    oracle[sid]["requested_lines"][0]["sku"] = "DL-012"
    item = next(s for s in scenarios if s["id"] == sid)
    item["turns"][-1]["text"] = "3 DL-012"
    oracle[sid]["requested_lines"][0]["quantity"] = 3
    assert any("not all supported" in error for error in dataset.validate(scenarios, oracle))


def test_validator_rejects_a_family_crossing_the_holdout_boundary(loaded):
    """Moving one member of a family to the other split would leak paraphrases across the boundary."""
    scenarios, oracle = loaded
    holdout = next(s for s in scenarios if s["split"] == "holdout")
    holdout["split"] = "development"
    errors = dataset.validate(scenarios, oracle)
    assert any("crosses" in error for error in errors)


def test_validator_rejects_media_confirming_a_field(loaded):
    """An oracle that lets audio or a photo advance past clarification contradicts the written-order policy."""
    scenarios, oracle = loaded
    item = next(s for s in scenarios if s["modality"] == "voice")
    oracle[item["id"]]["checkpoints"][0] = {
        "after_turn": 0,
        "action": "draft_quote",
        "reason": "complete_written_order",
    }
    assert any("media must stay" in error for error in dataset.validate(scenarios, oracle))


def test_validator_rejects_missing_oracle_entry(loaded):
    """Every scenario needs exactly one answer-key entry."""
    scenarios, oracle = loaded
    oracle.pop(scenarios[0]["id"])
    assert any("ids" in error for error in dataset.validate(scenarios, oracle))


def test_fingerprints_are_stable_hex_digests():
    """Evidence and a future freeze record can pin the exact fixture bytes."""
    prints = dataset.fingerprints()
    assert set(prints) == {"scenarios.json", "oracle.json"}
    assert all(len(value) == 64 for value in prints.values())


def test_staff_escalation_is_an_accepted_safe_alternative_for_media_only(loaded):
    """Every media checkpoint accepts staff escalation; the primary action stays clarify and exactness is tracked."""
    scenarios, oracle = loaded
    media = [(s, oracle[s["id"]]) for s in scenarios if s["modality"] != "text"]
    assert len(media) == 40 and all(
        e["checkpoints"][0]["also_acceptable"] == ["needs_staff"] for _, e in media
    )
    item, entry = media[0]
    escalated = ["needs_staff"] + [c["action"] for c in entry["checkpoints"][1:]]
    result = dataset.score(item, entry, escalated, entry["expected_subtotal"])
    assert result["status"] == "passed" and result["exact_match"] is False
    exact = dataset.score(
        item, entry, [c["action"] for c in entry["checkpoints"]], entry["expected_subtotal"]
    )
    assert exact["status"] == "passed" and exact["exact_match"] is True
    early_draft = ["draft_quote"] + [c["action"] for c in entry["checkpoints"][1:]]
    assert dataset.score(item, entry, early_draft, entry["expected_subtotal"])["status"] == "failed"
    text_item = next(s for s in scenarios if s["modality"] == "text")
    text_entry = oracle[text_item["id"]]
    assert all("also_acceptable" not in c for c in text_entry["checkpoints"])


def test_validator_rejects_a_draft_alternative_and_alternatives_on_text(loaded):
    """Nothing may excuse an early draft, and text checkpoints never list alternatives."""
    scenarios, oracle = loaded
    media = next(s for s in scenarios if s["modality"] == "voice")
    oracle[media["id"]]["checkpoints"][0]["also_acceptable"] = ["draft_quote"]
    assert any("only staff escalation" in error for error in dataset.validate(scenarios, oracle))
    scenarios, oracle = copy.deepcopy(dataset.load()[0]), copy.deepcopy(dataset.load()[1])
    text = next(s for s in scenarios if s["modality"] == "text")
    oracle[text["id"]]["checkpoints"][0]["also_acceptable"] = ["needs_staff"]
    assert any("only unreliable media" in error for error in dataset.validate(scenarios, oracle))


def test_freeze_blocks_the_holdout_until_pinned_unchanged_and_unspent(monkeypatch, tmp_path):
    """No freeze, a changed file or config, or a recorded run each forbid a holdout run."""
    current = dataset.freeze_fingerprints()
    assert set(current) == {"fixtures", "code", "model_configuration"} and current["code"]
    assert any(path.startswith("app/agents/luma_agent/nodes/") for path in current["code"])
    assert dataset.freeze_problems(None, current) == ["no freeze record exists"]
    record = {**copy.deepcopy(current), "holdout_runs": []}
    assert dataset.freeze_problems(record, current) == []
    drifted = copy.deepcopy(current)
    changed = next(iter(drifted["code"]))
    drifted["code"][changed] = "0" * 64
    assert any("code changed" in p and changed in p for p in dataset.freeze_problems(record, drifted))
    drifted = copy.deepcopy(current)
    drifted["model_configuration"]["openai_model"] = "another-model"
    assert any("model_configuration" in p for p in dataset.freeze_problems(record, drifted))
    drifted = copy.deepcopy(current)
    drifted["fixtures"]["oracle.json"] = "1" * 64
    assert any("oracle.json" in p for p in dataset.freeze_problems(record, drifted))
    spent = {**record, "holdout_runs": [{"run": "x"}]}
    assert any("already consumed" in p for p in dataset.freeze_problems(spent, current))
