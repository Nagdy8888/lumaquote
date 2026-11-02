"""Operator retention against real PostgreSQL, private Storage and LangGraph checkpoints (isolated tenant)."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import psycopg
from luma.core.storage import get_file
from psycopg.rows import dict_row
from test_graph_restart import pending, run_next
from test_manual_workflow import create_request, get_detail, make_draft, post
from test_voice_intake import upload, wav_bytes

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import retention  # noqa: E402

NOW = datetime.now(UTC)


def one(env, sql, *args):
    """Run a privileged query against this tenant and return its first row."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        return conn.execute(sql, args).fetchone()


def age(env, days_media=None, days_conversation=None):
    """Backdate this tenant's rows so retention sees them as old without waiting."""
    with psycopg.connect(env["dsn"]) as conn:
        if days_media is not None:
            conn.execute(
                "update luma.media set created_at=%s where company_id=%s",
                (NOW - timedelta(days=days_media), env["company"]),
            )
        if days_conversation is not None:
            old = NOW - timedelta(days=days_conversation)
            conn.execute(
                "update luma.conversations set updated_at=%s where company_id=%s", (old, env["company"])
            )
            conn.execute("update luma.audit set created_at=%s where company_id=%s", (old, env["company"]))


def test_runtime_media_is_deleted_after_seven_days_but_text_and_thread_remain(environment):
    """A dry run changes nothing; execute removes the private objects once, stamps the row and keeps the conversation."""
    env = environment
    cid = create_request(env)
    uploaded = upload(env, cid, wav_bytes())
    assert uploaded.status_code == 200
    media = one(env, "select * from luma.media where company_id=%s", env["company"])
    company = UUID(str(env["company"]))
    assert get_file(media["original_path"]) is not None
    age(env, days_media=6)
    assert retention.run(company, NOW, execute=True)["media"]["media_rows"] == 0  # six days old: kept
    age(env, days_media=8)
    dry = retention.run(company, NOW, execute=False)
    assert dry["media"] == {"media_rows": 1, "objects": 1} and dry["mode"] == "dry-run"
    assert get_file(media["original_path"]) is not None  # a dry run deletes nothing
    done = retention.run(company, NOW, execute=True)
    assert done["media"]["media_rows"] == 1
    assert get_file(media["original_path"]) is None
    assert (
        one(env, "select purged_at from luma.media where company_id=%s", env["company"])["purged_at"]
        is not None
    )
    assert retention.run(company, NOW, execute=True)["media"] == {
        "media_rows": 0,
        "objects": 0,
    }  # rerun is a no-op
    assert one(env, "select count(*) n from luma.conversations where company_id=%s", env["company"])["n"] == 1


def test_idle_conversations_are_deleted_with_everything_attached_and_unfinished_work_is_skipped(environment):
    """90+ day idle data goes children-first including objects and checkpoints; fresh and busy ones remain."""
    env = environment
    old = create_request(env)
    quote = make_draft(env, old)
    assert (
        post(
            env, f"/conversations/{old}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 200
    )
    assert env["api"].get(f"/api/quotes/{quote['id']}/pdf", headers=env["headers"]).status_code == 200
    pdf_path = f"{env['company']}/quotes/{quote['id']}.pdf"
    env["files"].append(pdf_path)
    run_next(env, old)
    assert pending(env, old) is not None
    fresh = create_request(env)
    busy = create_request(env)
    company = UUID(str(env["company"]))
    age(env, days_conversation=100)
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute("update luma.conversations set updated_at=now() where id=%s", (fresh,))
        conn.execute("update luma.jobs set status='done' where conversation_id in (%s,%s)", (old, fresh))
        conn.execute("update luma.outbox set status='local_delivered' where conversation_id=%s", (old,))
        conn.execute("update luma.drive_exports set status='blocked' where company_id=%s", (env["company"],))
    dry = retention.run(company, NOW, execute=False)
    assert dry["conversations"]["conversations"] == 1 and dry["skipped_unfinished_conversations"] == 1
    assert get_file(pdf_path) is not None and get_detail(env, old)["quote"]
    report = retention.run(company, NOW, execute=True)
    assert report["conversations"]["conversations"] == 1
    assert get_file(pdf_path) is None
    gone = {
        "conversations": "select count(*) n from luma.conversations where id=%s",
        "messages": "select count(*) n from luma.messages where conversation_id=%s",
        "quotes": "select count(*) n from luma.quotes where conversation_id=%s",
        "outbox": "select count(*) n from luma.outbox where conversation_id=%s",
        "jobs": "select count(*) n from luma.jobs where conversation_id=%s",
        "approvals": "select count(*) n from luma.approvals where quote_id=%s",
        "drive_exports": "select count(*) n from luma.drive_exports where quote_id=%s",
    }
    for table, sql in gone.items():
        target = quote["id"] if table in ("approvals", "drive_exports") else old
        assert one(env, sql, target)["n"] == 0, table
    assert (
        one(env, "select count(*) n from luma.operations where split_part(action,':',2)=%s", str(old))["n"]
        == 0
    )
    assert pending(env, old) == ()  # the checkpoint thread was deleted
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        rows = conn.execute(
            "select id from luma.conversations where company_id=%s", (env["company"],)
        ).fetchall()
    assert {str(row["id"]) for row in rows} == {str(fresh), str(busy)}
    assert retention.run(company, NOW, execute=True)["conversations"]["conversations"] == 0


def test_retention_refuses_unknown_company_and_foreign_objects(environment):
    """An unknown company id fails, and the storage helper refuses paths outside the company prefix."""
    import pytest
    from luma.core.storage import delete_files

    with pytest.raises(RuntimeError):
        retention.run(UUID(int=1), NOW, execute=False)
    with pytest.raises(ValueError):
        delete_files(str(environment["company"]), ["someone-else/quotes/x.pdf"])
    with pytest.raises(ValueError):
        delete_files(str(environment["company"]), [f"{environment['company']}/../other/x"])
