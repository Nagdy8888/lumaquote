"""Claude Code hook guards that enforce AGENTS.md rules R6, R14 and R15 (decision D32).

Wired in `.claude/settings.json`; each mode reads the hook's JSON payload from stdin:

- `stop`  (Stop hook, R14 and R8-R10): when application, script, test, migration or Apps Script
  files differ from HEAD, finishing is blocked unless `docs/WORK_LOG.md` changed AND at least one
  other documentation file changed (a `docs/reference/` guide, another `docs/` page, a README or
  `gas/README.md`). It also runs `scripts/check_docs.py` and `scripts/skills.py check`. A second
  stop attempt in the same chain (`stop_hook_active`) is allowed so the agent can report a blocker
  instead of looping forever.
- `edit`  (PostToolUse on Edit/Write, R6): warns when the edited file now has more than 30 deleted
  lines against HEAD, so accidental section loss is noticed immediately.
- `bash`  (PreToolUse on Bash, R15): blocks force-push, `git reset --hard`, rebases, amends,
  history rewrites, hook bypass and deployment commands before they run.

Exit code 2 with a message on stderr is Claude Code's "block / tell the model" signal; exit 0
allows. The guards only read git state and run read-only checks; they never modify files.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE_PREFIXES = ("app/", "scripts/", "tests/", "supabase/", "gas/", "package.json")
DOC_PATTERN = re.compile(
    r"^(docs/(?!WORK_LOG\.md$).+|README\.md|LOCAL_DEVELOPMENT\.md|gas/README\.md|app/.+\.md)$"
)
DELETION_LIMIT = 30
BLOCKED_COMMANDS = [
    (r"git\s+push\b[^\n;&|]*(--force\b|--force-with-lease\b|\s-f\b|\s\+\S)", "force-push"),
    (r"git\s+reset\s+[^\n;&|]*--hard", "git reset --hard"),
    (r"git\s+rebase\b", "rebase (history rewrite)"),
    (r"git\s+commit\b[^\n;&|]*--amend", "commit --amend (history rewrite)"),
    (r"git\s+(filter-branch|filter-repo)\b", "history rewrite"),
    (r"--no-verify\b", "hook bypass (--no-verify)"),
    (
        r"\b(vercel\s+(deploy|--prod)|wrangler\s+deploy|supabase\s+(db\s+push|link|functions\s+deploy)|clasp\s+deploy|gcloud\s+\S+\s+deploy|npm\s+run\s+deploy)\b",
        "deployment",
    ),
]


def payload() -> dict:
    """Read the hook's JSON input from stdin; an empty or invalid payload is treated as {}."""
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def changed_paths() -> list[str]:
    """Return repository-relative paths that differ from HEAD (staged, unstaged or untracked)."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    paths = []
    for line in result.stdout.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        paths.append(path.replace("\\", "/"))
    return paths


def run_check(arguments: list[str]) -> str:
    """Run one read-only project check with the project interpreter; return its output on failure."""
    result = subprocess.run(
        ["node", str(ROOT / "scripts" / "python.cjs"), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return "" if result.returncode == 0 else (result.stdout + result.stderr).strip()


def block(message: str) -> int:
    """Print a rule-naming message for the model and return Claude Code's blocking exit code."""
    print(message, file=sys.stderr)
    return 2


def stop(data: dict) -> int:
    """R14: require a work-log entry plus a documentation update for code changes; run fast checks."""
    if data.get("stop_hook_active"):
        return 0
    paths = changed_paths()
    code = [p for p in paths if p.startswith(CODE_PREFIXES) and not p.endswith(".md")]
    problems = []
    if code:
        if "docs/WORK_LOG.md" not in paths:
            problems.append(
                "R14: code changed but docs/WORK_LOG.md has no new entry (use the template in AGENTS.md)."
            )
        if not any(DOC_PATTERN.match(p) for p in paths):
            problems.append(
                "R14: code changed but no documentation was updated or added "
                "(update the owning docs/reference/ guide, or add one and link it from docs/README.md)."
            )
    for arguments in (["scripts/check_docs.py"], ["scripts/skills.py", "check"]):
        output = run_check(arguments)
        if output:
            problems.append(f"{' '.join(arguments)} failed:\n{output[:1500]}")
    if not problems:
        return 0
    changed = ", ".join(code[:8]) + (" ..." if len(code) > 8 else "")
    return block(
        "Stop blocked by AGENTS.md rules.\n"
        + "\n".join(problems)
        + (f"\nChanged code: {changed}" if code else "")
    )


def edit(data: dict) -> int:
    """R6: warn (without undoing anything) when an edited file lost many lines against HEAD."""
    target = (data.get("tool_input") or {}).get("file_path")
    if not target:
        return 0
    result = subprocess.run(
        ["git", "diff", "--numstat", "HEAD", "--", target],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    for line in result.stdout.splitlines():
        added, deleted, _ = (line.split("\t") + ["", ""])[:3]
        if deleted.isdigit() and int(deleted) > DELETION_LIMIT:
            return block(
                f"R6 warning: {target} now has {deleted} deleted lines (+{added}) against HEAD. "
                "Check `git diff` for accidental loss; if intended, state why in the work log."
            )
    return 0


def bash(data: dict) -> int:
    """R15: block destructive git operations, hook bypass and deployment before they run."""
    command = (data.get("tool_input") or {}).get("command", "")
    for pattern, name in BLOCKED_COMMANDS:
        if re.search(pattern, command):
            return block(f"R15: blocked {name}. AGENTS.md forbids it; ask the user if it is truly required.")
    return 0


def main() -> int:
    """Dispatch on the mode argument (`stop`, `edit`, `bash`); unknown modes allow the action."""
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = {"stop": stop, "edit": edit, "bash": bash}.get(mode)
    return handler(payload()) if handler else 0


if __name__ == "__main__":
    sys.exit(main())
