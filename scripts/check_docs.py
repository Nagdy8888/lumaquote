"""Enforce the documentation rules R8, R9 and R10 from AGENTS.md (decision D32).

Checks, each printed as `<rule> <path>[:line]: <problem>`:

- R8  Every project Markdown/JSON documentation file decodes as UTF-8, has no CRLF line
      endings and contains no mojibake sequences (UTF-8 bytes misread as Windows-1252).
- R8  Every relative Markdown link in project documentation resolves to an existing path.
- R9  Every evidence file in `docs/evidence/` created after 2026-11-03 starts with the common
      header (`date`, `commit`, `label`, `command`, `result`) and uses an allowed label.
- R10 Every ticked checkbox in `docs/IMPLEMENTATION_PLAN.md` links an existing evidence file on
      the same line; ticked phase 4 items must link evidence whose header label is `live`.

Read-only: it never rewrites files. Exit code 0 = clean, 1 = problems found.
Usage: node scripts/python.cjs scripts/check_docs.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVIDENCE = DOCS / "evidence"
PLAN = DOCS / "IMPLEMENTATION_PLAN.md"
LABELS = {"local", "local-substitute", "sandbox", "live", "synthetic"}
HEADER = ("date", "commit", "label", "command", "result")
# Mojibake markers: UTF-8 for an en dash, curly quotes, non-breaking space etc. decoded as cp1252.
MOJIBAKE = re.compile("â€|Ã[\u0080-¿ -ÿ]|Â ")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Evidence written before the header rule existed (2026-11-03); new files must carry the header.
LEGACY_EVIDENCE = {
    "api-boundaries-2026-11-02.json",
    "backup-restore-drill-2026-11-02.json",
    "catalog-development-baseline.json",
    "catalog-development-baseline-initial.json",
    "catalog-progress.json",
    "checkpoint-2026-11-02.json",
    "commit-checkpoint-2026-11-01.json",
    "diagram-documentation.json",
    "documentation-coverage.json",
    "evaluation-development-agent-2026-11-02.json",
    "evaluation-development-agent-run2-2026-11-02.json",
    "evaluation-development-baseline-2026-11-02.json",
    "google-gas-progress.json",
    "media-retrieval-recovery.json",
    "phase-1.json",
    "phase-1-accessibility.json",
    "phase-2.json",
    "phase-3-progress.json",
    "photo-progress.json",
    "secret-scan-2026-11-02.json",
    "semantic-progress.json",
    "written-confirmation-2026-11-01.json",
}


def documentation_files() -> list[Path]:
    """Return the project-owned documentation files these rules govern.

    Covers root Markdown, everything under `docs/` (Markdown and evidence JSON) and the GAS
    README. Imported skills are covered by `scripts/skills.py`; generated graph output and
    vendored folders are excluded.
    """
    files = list(ROOT.glob("*.md")) + list(DOCS.rglob("*.md")) + list(EVIDENCE.glob("*.json"))
    files.append(ROOT / "gas" / "README.md")
    return sorted(p for p in set(files) if p.exists())


def relative(path: Path) -> str:
    """Return a stable repository-relative posix path for messages."""
    return path.relative_to(ROOT).as_posix()


def check_encoding(path: Path) -> list[str]:
    """R8: report undecodable bytes, CRLF line endings and mojibake lines in one file."""
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        return [f"R8 {relative(path)}: not UTF-8 ({error.reason} at byte {error.start})"]
    problems = []
    if b"\r\n" in raw:
        problems.append(f"R8 {relative(path)}: CRLF line endings; convert to LF")
    for number, line in enumerate(text.splitlines(), 1):
        # Text inside inline code is a deliberate quotation (e.g. a rule naming the bad
        # sequence), so only prose outside backticks is checked.
        if MOJIBAKE.search(re.sub(r"`[^`]*`", "", line)):
            problems.append(f"R8 {relative(path)}:{number}: mojibake text; retype the character")
    return problems


def check_links(path: Path) -> list[str]:
    """R8: report relative Markdown links whose target path does not exist (anchors not checked)."""
    if path.suffix != ".md":
        return []
    problems = []
    in_code = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        if in_code:
            continue
        for target in LINK.findall(line):
            if re.match(r"^[a-z]+:|^#|^<", target):
                continue
            if not (path.parent / target.split("#")[0]).exists():
                problems.append(f"R8 {relative(path)}:{number}: broken link {target}")
    return problems


def evidence_header(path: Path) -> dict | None:
    """Return the parsed evidence object when it is a JSON object, otherwise None."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def check_evidence(path: Path) -> list[str]:
    """R9: require the common header and an allowed label in evidence created after the rule."""
    if path.name in LEGACY_EVIDENCE:
        return []
    data = evidence_header(path)
    if data is None:
        return [f"R9 {relative(path)}: evidence must be a JSON object"]
    problems = [f"R9 {relative(path)}: missing header field '{key}'" for key in HEADER if key not in data]
    if "label" in data and data["label"] not in LABELS:
        problems.append(f"R9 {relative(path)}: label '{data['label']}' is not one of {sorted(LABELS)}")
    return problems


def check_plan() -> list[str]:
    """R10: ticked plan items need linked evidence; ticked phase 4 items need `live` evidence."""
    problems = []
    phase = None
    for number, line in enumerate(PLAN.read_text(encoding="utf-8").splitlines(), 1):
        heading = re.match(r"^## (\d)\.", line)
        if heading:
            phase = int(heading.group(1))
        elif line.startswith("## "):
            phase = None
        if not line.startswith("- [x]"):
            continue
        targets = [t for t in LINK.findall(line) if t.startswith("evidence/")]
        existing = [
            PLAN.parent / t.split("#")[0] for t in targets if (PLAN.parent / t.split("#")[0]).exists()
        ]
        if not existing:
            problems.append(f"R10 {relative(PLAN)}:{number}: ticked item without an existing evidence link")
        elif phase == 4:
            labels = {(evidence_header(p) or {}).get("label") for p in existing}
            if "live" not in labels:
                problems.append(f"R10 {relative(PLAN)}:{number}: phase 4 item needs evidence labeled 'live'")
    return problems


def main() -> int:
    """Run every check over the governed files and print one line per problem."""
    problems = []
    for path in documentation_files():
        problems += check_encoding(path)
        if not any(p.startswith(f"R8 {relative(path)}: not UTF-8") for p in problems):
            problems += check_links(path)
        if path.parent == EVIDENCE:
            problems += check_evidence(path)
    problems += check_plan()
    for problem in problems:
        print(problem)
    if not problems:
        print(f"Documentation rules R8-R10 passed for {len(documentation_files())} files.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
