"""Run the offline exact-order baseline over the 80-scenario set and report honest denominators.

This is NOT the agent evaluation. The system under test is the deterministic
baseline: the shared written-order grammar, the field-confirmation gate, a
read-only catalog lookup and the same supported/unsupported rule that
`nodes/workflow.prepare` applies. No model, transcription, vision, WhatsApp,
Google or LangSmith call is made and nothing is written to the database.
Voice and photo scenarios are reported as not run because no audio or image
assets exist yet. Only the development split can be run; the holdout is
refused until a code/prompt/fixture freeze record exists.
"""

import argparse
import json
import math
import statistics
import sys
import time
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import evaluation_dataset as dataset
from luma.core.config import settings
from luma.core.database import database
from luma.features.catalog.retrieval import search_catalog
from luma.features.catalog.schemas import CatalogSearch
from luma.features.quotations.rules import calculate
from luma_agent.nodes.extraction import baseline_extract
from luma_agent.requirements import clarification_for
from psycopg.conninfo import conninfo_to_dict

SCOPE = (
    "Offline exact-order baseline over the development split. Not the agent, not the frozen holdout, "
    "no model/audio/vision/provider call. Voice and photo scenarios are not run (no assets exist)."
)


def load_catalog(conn, company: UUID) -> dict[str, dict]:
    """Read current products from non-retired sources, the same visibility rule `prepare` uses."""
    rows = conn.execute(
        """select p.*,coalesce(sl.on_hand-sl.reserved,0) as available from luma.products p
        join luma.sources s on s.company_id=p.company_id and s.id=p.source_id
        left join luma.stock_levels sl on sl.company_id=p.company_id and sl.product_id=p.id
        where p.company_id=%s and s.retired_at is null""",
        (company,),
    ).fetchall()
    return {row["sku"]: row for row in rows}


def decide(catalog: dict, history: list[dict]) -> tuple[str, str | None]:
    """Return the baseline action and subtotal for the customer turns seen so far (newest first in `history`).

    The confirmation gate runs first; only a complete written order reaches the
    catalog. Any unsupported line sends the whole order to staff, mirroring
    `prepare`. No substitute is ever chosen and nothing is approved or sent.
    """
    result = baseline_extract(history[0]["body"])
    if clarification_for(result, history, media=False) is not None:
        return "clarify", None
    lines = []
    for line in result.lines:
        product = catalog.get(line.sku)
        if (
            product is None
            or product["discontinued"]
            or product["available"] < line.quantity
            or line.quantity % product["pack_size"]
        ):
            return "needs_staff", None
        lines.append({**product, "product_id": product["id"], "quantity": line.quantity})
    quote = calculate(lines, Decimal(0), Decimal(0), "salesperson")
    return "draft_quote", quote["subtotal"]


def run_scenario(conn, company: UUID, catalog: dict, item: dict, entry: dict) -> dict:
    """Replay one text scenario turn by turn against the baseline and compare each checkpoint to the oracle."""
    history, observed, subtotal = [], [], None
    start = time.perf_counter()
    for turn in item["turns"]:
        history.insert(0, {"kind": "text", "body": turn["text"]})
        action, subtotal = decide(catalog, history)
        observed.append(action)
    milliseconds = (time.perf_counter() - start) * 1000
    replies = []
    if entry["retrieval"]:
        hits = search_catalog(conn, company, CatalogSearch(query=item["turns"][0]["text"]))
        replies = [" ".join(hit.sku for hit in hits[:5])]
    result = dataset.score(item, entry, observed, subtotal, replies)
    result["decision_ms"] = round(milliseconds, 3)
    return result


def summarize(scenarios: list[dict], results: list[dict]) -> dict:
    """Aggregate counts by modality with explicit run/not-run denominators and the plan's target measures."""
    ran = {result["id"]: result for result in results}
    by_modality = {}
    for modality in dataset.MODALITY_TOTALS:
        selected = [item for item in scenarios if item["modality"] == modality]
        executed = [ran[item["id"]] for item in selected if item["id"] in ran]
        by_modality[modality] = {
            "scenarios": len(selected),
            "run": len(executed),
            "not_run": len(selected) - len(executed),
            "passed": sum(result["status"] == "passed" for result in executed),
            "failed": sum(result["status"] == "failed" for result in executed),
        }
    ambiguity = [
        r["first_turn_acts_on_ambiguity"] for r in results if r["first_turn_acts_on_ambiguity"] is not None
    ]
    recalls = [r["retrieval_recall_at_5"] for r in results if r["retrieval_recall_at_5"] is not None]
    times = sorted(result["decision_ms"] for result in results)
    return {
        "by_modality": by_modality,
        "workflow_success": {"passed": sum(r["status"] == "passed" for r in results), "run": len(results)},
        "ambiguity_acted_on": {"acted": sum(ambiguity), "applicable_run": len(ambiguity)},
        "unsupported_final_lines": sum(r["unsupported_final_line"] for r in results),
        "unauthorized_sends": "not measured: the baseline cannot send",
        "retrieval_recall_at_5": {"found": sum(recalls), "applicable_run": len(recalls)},
        "decision_latency_ms": {
            "median": round(statistics.median(times), 3) if times else None,
            "p95": round(times[math.ceil(len(times) * 0.95) - 1], 3) if times else None,
        },
    }


def evaluate(company: UUID, output: Path) -> int:
    """Run the development text scenarios read-only, write credential-free evidence and return a process status."""
    params = conninfo_to_dict(settings().luma_worker_database_url.get_secret_value())
    if params.get("host") not in ("127.0.0.1", "localhost") or params.get("port") != "55322":
        raise RuntimeError("Scenario evaluation requires this project's isolated local database.")
    scenarios, oracle = dataset.load()
    problems = dataset.validate(scenarios, oracle)
    if problems:
        raise RuntimeError("Dataset is inconsistent: " + "; ".join(problems[:5]))
    development = [item for item in scenarios if item["split"] == "development"]
    with database(worker=True) as conn:
        tenant = conn.execute("select synthetic from luma.companies where id=%s", (company,)).fetchone()
        if not tenant or not tenant["synthetic"]:
            raise RuntimeError("Evaluation is restricted to an explicitly synthetic supplier.")
        catalog = load_catalog(conn, company)
        results = [
            run_scenario(conn, company, catalog, item, oracle[item["id"]])
            for item in development
            if item["modality"] == "text"
        ]
    report = {
        "scope": SCOPE,
        "split": "development",
        "holdout_consumed": False,
        "fixtures_sha256": dataset.fingerprints(),
        "denominators": dataset.denominators(scenarios),
        "summary": summarize(development, results),
        "targets_from_plan": {
            "retrieval_recall_at_5": ">=95% on applicable labeled cases",
            "workflow_success": ">=90% across the full suite",
            "unauthorized_sends": 0,
            "ambiguity": "every ambiguous consequential field asks or escalates",
            "status": "not assessed: voice/photo not run, holdout not run, agent not run",
        },
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "output": str(output), "scope": "offline baseline only"}))
    return 1 if any(result["status"] == "failed" for result in results) else 0


def main() -> None:
    """Require an explicit synthetic company and evidence path; the holdout split cannot be selected."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", type=UUID, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split", choices=["development"], default="development")
    args = parser.parse_args()
    sys.exit(evaluate(args.company, args.output))


if __name__ == "__main__":
    main()
