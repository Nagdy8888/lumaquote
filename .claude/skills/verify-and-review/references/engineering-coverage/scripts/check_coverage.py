"""Validate coverage metadata; never a substitute for reviewing evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

CATALOG = Path(__file__).resolve().parents[1] / "references" / "concepts.json"
STATES = {"NotAssessed", "Planned", "Blocked", "Covered", "NotApplicable"}
KINDS = {"code", "config", "design", "test", "runtime"}
RESULTS = {"observed", "passed", "failed", "not_run"}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    items = catalog.get("concepts", [])
    ids = [item.get("id") for item in items]
    if not items or any(not text(value) for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("Catalog must have nonempty unique IDs")
    fields = {"id", "concept", "definition", "example_failure", "verification", "source"}
    if any(not fields.issubset(item) or any(not text(item[key]) for key in fields) for item in items):
        raise ValueError("Catalog contains an incomplete concept")
    return items


def validate(ledger, workspace, release=False):
    errors = []
    expected = {item["id"] for item in load_catalog()}
    if not isinstance(ledger, dict):
        return ["Ledger must be an object"]
    if ledger.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for field in ("scope", "revision", "environment"):
        if not text(ledger.get(field)):
            errors.append(f"{field} must be a nonempty string")
    rows = ledger.get("assessments")
    if not isinstance(rows, list):
        return errors + ["assessments must be an array"]
    if any(not isinstance(row, dict) for row in rows):
        return errors + ["Every assessment must be an object"]
    ids = [row.get("id") for row in rows]
    if any(not text(value) for value in ids):
        return errors + ["Every assessment must have a string ID"]
    if set(ids) != expected or len(ids) != len(expected):
        errors.append("Assessments must cover every catalog ID exactly once")
    workspace = Path(workspace).resolve()
    for row in rows:
        prefix = row["id"]
        state = row.get("status")
        if not isinstance(state, str) or state not in STATES:
            errors.append(f"{prefix}: invalid status")
            continue
        if not text(row.get("reason")):
            errors.append(f"{prefix}: reason is required")
        evidence = row.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{prefix}: evidence must be an array")
            continue
        implementation = behavioral = False
        for item in evidence:
            if not isinstance(item, dict):
                errors.append(f"{prefix}: invalid evidence object")
                continue
            kind, result = item.get("kind"), item.get("result")
            if not isinstance(kind, str) or kind not in KINDS or not isinstance(result, str) or result not in RESULTS:
                errors.append(f"{prefix}: invalid evidence kind/result")
                continue
            relative = item.get("path")
            if not text(relative):
                errors.append(f"{prefix}: evidence path is required")
            else:
                artifact = workspace / relative
                if Path(relative).is_absolute() or not artifact.resolve().is_relative_to(workspace) or not artifact.is_file():
                    errors.append(f"{prefix}: evidence must be an existing workspace file")
            if not text(item.get("revision")) or not text(item.get("environment")):
                errors.append(f"{prefix}: evidence revision and environment are required")
            if state == "Covered":
                if item.get("revision") != ledger.get("revision") or item.get("environment") != ledger.get("environment"):
                    errors.append(f"{prefix}: stale or different-environment evidence")
                if result not in {"observed", "passed"}:
                    errors.append(f"{prefix}: Covered includes failed or unrun evidence")
            implementation |= kind in {"code", "config", "design"} and result in {"observed", "passed"}
            behavioral |= kind in {"test", "runtime"} and result == "passed"
        if state == "Covered" and not (implementation and behavioral):
            errors.append(f"{prefix}: Covered requires implementation and passing behavioral evidence")
        if release and state not in {"Covered", "NotApplicable"}:
            errors.append(f"{prefix}: unresolved release assessment")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", nargs="?")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--init", dest="initialize")
    parser.add_argument("--scope")
    parser.add_argument("--revision")
    parser.add_argument("--environment")
    args = parser.parse_args()
    try:
        concepts = load_catalog()
        if args.catalog_only:
            print(f"Catalog valid: {len(concepts)} concepts. No application assessment performed.")
            return 0
        if args.initialize:
            if not all(text(v) for v in (args.scope, args.revision, args.environment)):
                parser.error("--init requires --scope, --revision, and --environment")
            target = Path(args.initialize)
            workspace = Path(args.workspace).resolve()
            if not target.resolve().is_relative_to(workspace):
                parser.error("New ledger must be inside --workspace")
            target.parent.mkdir(parents=True, exist_ok=True)
            ledger = {
                "schema_version": 1, "scope": args.scope, "revision": args.revision,
                "environment": args.environment,
                "assessments": [
                    {"id": item["id"], "status": "NotAssessed",
                     "reason": "Applicability and enforcement have not been inspected.", "evidence": []}
                    for item in concepts
                ],
            }
            with target.open("x", encoding="utf-8") as handle:
                json.dump(ledger, handle, indent=2)
                handle.write("\n")
            print(f"Initialized {len(concepts)} unassessed concepts; this is not release-ready.")
            return 0
        if not args.ledger:
            parser.error("Provide a ledger, --init, or --catalog-only")
        ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8-sig"))
        errors = validate(ledger, args.workspace, args.release)
        for error in errors:
            print(error, file=sys.stderr)
        if errors:
            return 1
        counts = dict(Counter(row["status"] for row in ledger["assessments"]))
        print(f"Ledger metadata valid: {counts}")
        print("Inspect actual evidence and applicability; this is not a security certification.")
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f"Coverage validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
