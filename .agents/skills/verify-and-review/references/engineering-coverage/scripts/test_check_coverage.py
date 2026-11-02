"""Behavioral checks for preventing unsupported coverage claims."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_coverage import load_catalog, validate


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "implementation.txt").write_text("Fixture implementation", encoding="utf-8")
        (self.root / "result.txt").write_text("Fixture runtime verification result", encoding="utf-8")
        self.ledger = {
            "schema_version": 1, "scope": "Validator fixture, not the actual app",
            "revision": "fixture-1", "environment": "isolated-test",
            "assessments": [
                {"id": item["id"], "status": "NotApplicable",
                 "reason": "Excluded from this synthetic validator fixture.", "evidence": []}
                for item in load_catalog()
            ],
        }

    def covered(self):
        row = self.ledger["assessments"][0]
        row.update(status="Covered", reason="Fixture evidence only.")
        row["evidence"] = [
            {"kind": kind, "path": path, "result": result,
             "revision": "fixture-1", "environment": "isolated-test"}
            for kind, path, result in [
                ("code", "implementation.txt", "observed"),
                ("runtime", "result.txt", "passed"),
            ]
        ]
        return row

    def test_complete_metadata_is_accepted(self):
        self.covered()
        self.assertEqual(validate(self.ledger, self.root, True), [])

    def test_partial_or_duplicate_inventory_is_rejected(self):
        partial = copy.deepcopy(self.ledger)
        partial["assessments"].pop()
        self.assertTrue(validate(partial, self.root))
        self.ledger["assessments"][-1] = copy.deepcopy(self.ledger["assessments"][0])
        self.assertTrue(validate(self.ledger, self.root))

    def test_unproved_covered_and_unjustified_exclusion_are_rejected(self):
        self.ledger["assessments"][0]["status"] = "Covered"
        self.assertTrue(validate(self.ledger, self.root))
        self.ledger["assessments"][0].update(status="NotApplicable", reason="")
        self.assertTrue(validate(self.ledger, self.root))

    def test_missing_and_external_artifacts_are_rejected(self):
        row = self.covered()
        row["evidence"][1]["path"] = "missing-result.txt"
        self.assertTrue(validate(self.ledger, self.root))
        row["evidence"][1]["path"] = "../outside-result.txt"
        self.assertTrue(validate(self.ledger, self.root))

    def test_stale_or_other_environment_evidence_is_rejected(self):
        row = self.covered()
        row["evidence"][1]["revision"] = "fixture-old"
        self.assertTrue(validate(self.ledger, self.root))
        row["evidence"][1].update(revision="fixture-1", environment="other")
        self.assertTrue(validate(self.ledger, self.root))

    def test_failed_evidence_cannot_be_hidden_under_covered(self):
        row = self.covered()
        row["evidence"].append(dict(row["evidence"][1], result="failed"))
        self.assertTrue(validate(self.ledger, self.root))

    def test_work_can_progress_but_release_rejects_unfinished(self):
        self.ledger["assessments"][0]["status"] = "Planned"
        self.assertEqual(validate(self.ledger, self.root), [])
        self.assertTrue(validate(self.ledger, self.root, True))

    def test_initializer_and_release_cli(self):
        script = Path(__file__).with_name("check_coverage.py")
        ledger = self.root / "coverage.json"
        command = [sys.executable, str(script), "--workspace", str(self.root),
                   "--init", str(ledger), "--scope", "Fixture only",
                   "--revision", "fixture-1", "--environment", "isolated-test"]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        data = json.loads(ledger.read_text())
        self.assertEqual(len(data["assessments"]), len(load_catalog()))
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertNotEqual(subprocess.run(
            [sys.executable, str(script), str(ledger), "--workspace", str(self.root), "--release"],
            capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
