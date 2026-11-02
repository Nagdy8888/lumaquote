"""Record or check the pre-holdout freeze of fixtures, agent code and model configuration.

`--write` creates `tests/fixtures/evaluation/freeze.json` (refuses to overwrite one that already
records a holdout run). `--check` reports whether the current tree still matches. Only the freeze
file's presence and match, plus the absence of a recorded run, allow a holdout run; it never
runs anything itself and never touches a provider.
"""

import argparse
import json
import sys
from datetime import UTC, datetime

import evaluation_dataset as dataset


def write() -> int:
    """Pin the current fixtures/code/config; refuse if a holdout run is already recorded."""
    existing = dataset.load_freeze()
    if existing and existing.get("holdout_runs"):
        print("Refusing to refreeze: a holdout run is recorded. Reserve new cases instead.")
        return 2
    record = {"created": datetime.now(UTC).isoformat(), **dataset.freeze_fingerprints(), "holdout_runs": []}
    dataset.FREEZE_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Freeze recorded for {len(record['code'])} code files and {len(record['fixtures'])} fixtures.")
    return 0


def check() -> int:
    """Print every reason the holdout may not run, or confirm the freeze still holds."""
    problems = dataset.freeze_problems(dataset.load_freeze(), dataset.freeze_fingerprints())
    print("\n".join(problems) if problems else "Freeze holds; the holdout has not been run.")
    return 1 if problems else 0


def main() -> int:
    """Dispatch the requested action."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return write() if args.write else check()


if __name__ == "__main__":
    sys.exit(main())
