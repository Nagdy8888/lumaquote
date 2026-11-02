"""Rule R11: evaluation runs are scored only against the answer key pinned when they started."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import evaluation_dataset as dataset  # noqa: E402
import summarize_agent_run  # noqa: E402


def run_summarizer(monkeypatch, run: Path, output: Path, *extra: str) -> int:
    """Invoke the summarizer's CLI entry point with a temporary run directory and output path."""
    monkeypatch.setattr(sys, "argv", ["summarize", "--run", str(run), "--output", str(output), *extra])
    return summarize_agent_run.main()


def pin(run: Path, fingerprints: dict) -> None:
    """Write the run-start record the live harness creates before the first scenario."""
    run.mkdir(parents=True, exist_ok=True)
    (run / "run.json").write_text(json.dumps({"fixtures_sha256": fingerprints}), encoding="utf-8")


def test_matching_pin_is_scored_normally(tmp_path, monkeypatch):
    """A run pinned to the current fixtures is summarized and not labeled post-hoc."""
    run, output = tmp_path / "run", tmp_path / "out.json"
    pin(run, dataset.fingerprints())
    assert run_summarizer(monkeypatch, run, output) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["post_hoc"] is False
    assert report["run_fixtures_sha256"] == report["fixtures_sha256"]


@pytest.mark.parametrize("pinned", [None, {"scenarios.json": "0" * 64, "oracle.json": "1" * 64}])
def test_changed_or_missing_pin_is_refused_without_post_hoc(tmp_path, monkeypatch, pinned):
    """A moved answer key (or no pin at all) is refused and writes no evidence."""
    run, output = tmp_path / "run", tmp_path / "out.json"
    run.mkdir()
    if pinned is not None:
        pin(run, pinned)
    assert run_summarizer(monkeypatch, run, output) == 1
    assert not output.exists()


def test_post_hoc_flag_labels_the_report(tmp_path, monkeypatch):
    """With --post-hoc the report is written, labeled, and keeps both hash sets visible."""
    run, output = tmp_path / "run", tmp_path / "out.json"
    pin(run, {"scenarios.json": "0" * 64, "oracle.json": "1" * 64})
    assert run_summarizer(monkeypatch, run, output, "--post-hoc") == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["post_hoc"] is True
    assert report["run_fixtures_sha256"]["oracle.json"] == "1" * 64
