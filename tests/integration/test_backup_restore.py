"""Backup/restore drill on a populated isolated tenant: dump, restore into a scratch database, compare, clean up.

Requires the local Supabase container and the docker CLI. The source database is only read; the drill
creates and removes its own scratch database and scratch Storage prefix.
"""

import os
import sys
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from test_graph_restart import pending, run_next
from test_manual_workflow import create_request, make_draft, post
from test_voice_intake import upload, wav_bytes

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import backup_restore_drill as drill  # noqa: E402


def test_populated_tenant_restores_identically_with_checkpoints_and_objects(environment, tmp_path):
    """Approved quote, stored PDF, uploaded audio and a graph checkpoint all survive dump and restore unchanged."""
    env = environment
    cid = create_request(env)
    quote = make_draft(env, cid)
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 200
    )
    assert env["api"].get(f"/api/quotes/{quote['id']}/pdf", headers=env["headers"]).status_code == 200
    env["files"].append(f"{env['company']}/quotes/{quote['id']}.pdf")
    other = create_request(env)
    assert upload(env, other, wav_bytes()).status_code == 200
    checkpointed = create_request(env)
    run_next(env, checkpointed)
    assert pending(env, checkpointed) == ("review",)
    output = Path(os.environ.get("LUMA_DRILL_EVIDENCE", tmp_path / "drill.json"))
    report = drill.run(UUID(str(env["company"])), output)
    assert report["restore_exit_code"] == 0 and report["database_identical"] is True
    assert report["objects_round_trip_identical"] is True and report["scratch_database_removed"] is True
    rows = report["source"]["rows"]
    assert (
        rows["approvals"] == 1 and rows["quotes"] == 2 and rows["media"] == 1 and rows["drive_exports"] == 1
    )
    assert report["objects"] >= 2 and sum(report["source"]["checkpoint_rows"].values()) > 0
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        assert (
            conn.execute("select count(*) n from pg_database where datname=%s", (drill.SCRATCH,)).fetchone()[
                "n"
            ]
            == 0
        )
