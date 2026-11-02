"""Aggregate one paid agent evaluation run into credential-free evidence with explicit denominators.

Input is the directory of per-scenario JSON records written by
`tests/integration/test_live_evaluation.py`. The summary never hides errors or
not-run scenarios: every modality shows scenarios, run, passed, failed, errored and
not run, and the plan's targets are compared only where the denominator supports it.
"""

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

import evaluation_dataset as dataset


def divergence(result: dict) -> dict | None:
    """Return the first checkpoint where the observed action differs from the answer key, or None."""
    for index, (want, got) in enumerate(
        zip(result["expected_actions"], result["observed_actions"], strict=False)
    ):
        if want != got:
            return {"turn": index, "expected": want, "observed": got}
    if result["expected_subtotal"] != result["observed_subtotal"]:
        return {
            "turn": len(result["observed_actions"]) - 1,
            "expected_subtotal": result["expected_subtotal"],
            "observed_subtotal": result["observed_subtotal"],
        }
    return None


def summarize(split: str, scenarios: list[dict], oracle: dict, results: dict[str, dict]) -> dict:
    """Build the evidence body from loaded scenarios and the records found for them."""
    chosen = [item for item in scenarios if item["split"] == split]
    modalities = {}
    for modality in dataset.MODALITY_TOTALS:
        group = [item for item in chosen if item["modality"] == modality]
        records = [results[item["id"]] for item in group if item["id"] in results]
        modalities[modality] = {
            "scenarios": len(group),
            "run": len(records),
            "not_run": len(group) - len(records),
            "passed": sum(r["status"] == "passed" for r in records),
            "failed": sum(r["status"] == "failed" for r in records),
            "errored": sum(r["status"] == "error" for r in records),
        }
    by_id = {item["id"]: item for item in scenarios}
    for record in results.values():
        if record["status"] != "error":
            rescored = dataset.score(
                by_id[record["id"]],
                oracle[record["id"]],
                record["observed_actions"],
                record["observed_subtotal"],
                record.get("replies", []),
            )
            record.update({key: rescored[key] for key in ("status", "exact_match", "retrieval_recall_at_5")})
    scored = [r for r in results.values() if r["status"] in ("passed", "failed")]
    ambiguity = [
        r["first_turn_acts_on_ambiguity"] for r in scored if r["first_turn_acts_on_ambiguity"] is not None
    ]
    recall = [r["retrieval_recall_at_5"] for r in scored if r["retrieval_recall_at_5"] is not None]
    times = sorted(r["decision_ms"] for r in scored)
    return {
        "scope": f"Paid live agent run, {split} split only; synthetic data; transcription/vision/Responses real, staff approval and delivery never executed.",
        "by_modality": modalities,
        "exact_primary_action_match": {
            "exact": sum(bool(r["exact_match"]) for r in scored),
            "scored": len(scored),
        },
        "workflow_success": {
            "passed": sum(r["status"] == "passed" for r in scored),
            "scored": len(scored),
            "errored": sum(r["status"] == "error" for r in results.values()),
        },
        "ambiguity_acted_on": {"acted": sum(ambiguity), "applicable_scored": len(ambiguity)},
        "retrieval_recall_at_5": {"found": sum(recall), "applicable_scored": len(recall)},
        "unsupported_final_lines": sum(
            bool(r["unsupported_final_line"]) or not r["quote_lines_all_supported"] for r in scored
        ),
        "unauthorized_sends": sum(r["unauthorized_sends"] for r in scored),
        "unresolved_usage_rows": sum(r["unresolved_usage"] for r in scored),
        "estimated_usage_usd": round(sum(r.get("usage_usd", 0.0) for r in results.values()), 6),
        "usage_note": "Conservative token-derived estimate from the app's own settlement, not provider billing.",
        "decision_latency_ms": {
            "median": round(statistics.median(times), 1) if times else None,
            "p95": round(times[math.ceil(len(times) * 0.95) - 1], 1) if times else None,
        },
        "failures": [
            {"id": r["id"], "modality": r["modality"], "divergence": divergence(r)}
            for r in sorted(scored, key=lambda x: x["id"])
            if r["status"] == "failed"
        ],
        "errors": [
            {"id": r["id"], "error": r.get("error")} for r in results.values() if r["status"] == "error"
        ],
    }


def main() -> int:
    """Read a run directory, write the evidence file and print the headline counts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split", choices=["development", "holdout"], default="development")
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    scenarios, oracle = dataset.load()
    results = {
        path.stem: json.loads(path.read_text(encoding="utf-8")) for path in sorted(args.run.glob("e*.json"))
    }
    report = {
        "split": args.split,
        "holdout_consumed": args.split == "holdout",
        "fixtures_sha256": dataset.fingerprints(),
        "denominators": dataset.denominators(scenarios),
        "note": args.note,
        "summary": summarize(args.split, scenarios, oracle, results),
        "results": [results[key] for key in sorted(results)],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "by_modality": report["summary"]["by_modality"],
                "workflow_success": report["summary"]["workflow_success"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
