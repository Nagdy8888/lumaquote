"""Check that no populated secret value from the ignored environment files appears in publishable output.

It reads secret-looking values (keys containing KEY, SECRET, TOKEN, PASSWORD, DSN or DATABASE_URL, at
least 12 characters) from `.env` and `.env.local`, then searches git-tracked files, the frontend build
output, retained check logs and evidence files for each value and for its URL-encoded and base64 forms.
It prints only the variable NAME and file path of a hit, never a value. Exit code 1 means a leak.

It proves these specific values are absent from these specific places on this machine at this time.
It does not find secrets it was not given, secrets in other branches/history, or provider-side copies.
"""

import base64
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SECRET_KEY = re.compile(r"(KEY|SECRET|TOKEN|PASSWORD|DSN|DATABASE_URL)", re.IGNORECASE)
PUBLIC_KEYS = re.compile(r"^(VITE_|SUPABASE_ANON_KEY$)")
SCAN_DIRS = ("app/frontend/dist", ".local/checks", "docs/evidence")


def load_secrets(files: list[Path]) -> dict[str, list[str]]:
    """Return variable name -> searchable forms for each populated secret-looking value."""
    found = {}
    for path in files:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            name, sep, value = line.partition("=")
            name, value = name.strip(), value.strip().strip("'\"")
            if not sep or not SECRET_KEY.search(name) or PUBLIC_KEYS.match(name) or len(value) < 12:
                continue
            forms = {value, quote(value, safe=""), base64.b64encode(value.encode()).decode().rstrip("=")}
            found[name] = sorted(form for form in forms if len(form) >= 12)
    return found


def tracked_files(root: Path) -> list[Path]:
    """List git-tracked files (the content that would be published)."""
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    return [root / name for name in out.decode().split("\0") if name]


def scan_files(paths: list[Path], secrets: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Return (variable name, path) for every file containing any form of a secret; values are never returned."""
    hits = []
    for path in paths:
        if not path.is_file() or path.stat().st_size > 20 * 1024 * 1024:
            continue
        text = path.read_bytes().decode("utf-8", errors="ignore")
        hits += [(name, str(path)) for name, forms in secrets.items() if any(form in text for form in forms)]
    return hits


def run(root: Path = ROOT) -> dict:
    """Scan tracked files and build/log/evidence directories; return a value-free report."""
    secrets = load_secrets([root / ".env", root / ".env.local"])
    paths = tracked_files(root)
    for folder in SCAN_DIRS:
        base = root / folder
        if base.is_dir():
            paths += [p for p in base.rglob("*") if p.is_file()]
    hits = scan_files(sorted(set(paths)), secrets)
    return {
        "secret_variables_checked": sorted(secrets),
        "files_scanned": len(set(paths)),
        "leaks": [{"variable": name, "file": Path(file).relative_to(root).as_posix()} for name, file in hits],
    }


def main() -> int:
    """Print the report and fail when any populated secret appears in a scanned location."""
    report = run()
    print(json.dumps(report, indent=2))
    return 1 if report["leaks"] else 0


if __name__ == "__main__":
    sys.exit(main())
