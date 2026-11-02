"""The secret scanner finds planted values in every encoding and never echoes a value."""

import base64
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import scan_secrets as scanner  # noqa: E402

SECRET = "sup3r-s3cret/value+with=chars-1234567890"


def make_repo(tmp_path, tracked_body):
    """Create a throwaway git repo with an ignored env file and one tracked file."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".env.local").write_text(
        f"SERVICE_API_KEY={SECRET}\nVITE_PUBLIC_KEY={SECRET}-public\nSHORT_TOKEN=abc\nPLAIN=value-that-is-long-enough\n",
        encoding="utf-8",
    )
    (tmp_path / "tracked.txt").write_text(tracked_body, encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)


def test_only_secret_looking_long_nonpublic_values_are_loaded(tmp_path):
    """Public Vite values, short values and non-secret names are not treated as secrets."""
    make_repo(tmp_path, "x")
    assert list(scanner.load_secrets([tmp_path / ".env.local"])) == ["SERVICE_API_KEY"]


def test_plain_urlencoded_and_base64_forms_are_detected_without_echoing_the_value(tmp_path):
    """A leak in any encoding is reported by variable name and path only."""
    for body in (SECRET, quote(SECRET, safe=""), base64.b64encode(SECRET.encode()).decode().rstrip("=")):
        make_repo(tmp_path, f"prefix {body} suffix")
        report = scanner.run(tmp_path)
        assert report["leaks"] == [{"variable": "SERVICE_API_KEY", "file": "tracked.txt"}]
        assert SECRET not in str(report) and "sup3r" not in str(report)


def test_clean_repo_reports_no_leaks(tmp_path):
    """Absence is reported as an empty leak list with the checked variable names."""
    make_repo(tmp_path, "nothing secret here")
    report = scanner.run(tmp_path)
    assert report["leaks"] == [] and report["secret_variables_checked"] == ["SERVICE_API_KEY"]
