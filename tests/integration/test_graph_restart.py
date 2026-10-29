"""Actual PostgreSQL checkpoints survive independent native worker processes and authorized staff participation."""

import os
import subprocess
import sys

import psycopg
import pytest
from langgraph.checkpoint.postgres import PostgresSaver
from luma.core.admission import enqueue
from luma.core.config import settings
from luma.core.database import database
from luma.features.media.persistence import complete_media
from luma_agent.graph import build_graph
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail, make_draft, post
from test_voice_intake import upload, wav_bytes


def run_next(env, cid):
    """Lease only this test's next job and process it in a fresh Python process with paid AI disabled."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        job = conn.execute(
            """update luma.jobs set status='running',fence=fence+1,lease_until=now()+interval '120 seconds'
            where id=(select id from luma.jobs where company_id=%s and conversation_id=%s
            and status='queued' order by created_at limit 1) returning id""",
            (env["company"], cid),
        ).fetchone()
    assert job
    code = """import sys
from luma.core.database import database
from luma_agent.runtime.conversations import process_conversation
from luma_agent.runtime.jobs import finish_job
with database(worker=True) as conn:
    job=conn.execute('select * from luma.jobs where id=%s',(sys.argv[1],)).fetchone()
process_conversation(job)
finish_job(job,'done')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(job["id"])],
        env={**os.environ, "ENABLE_PAID_AI": "false", "LANGSMITH_TRACING": "false"},
        capture_output=True,
        timeout=35,
    )
    assert result.returncode == 0, "The isolated worker process failed; provider payloads are withheld."


def pending(env, cid):
    """Read the actual persisted graph continuation through the same scoped thread identity as the worker."""
    with PostgresSaver.from_conn_string(settings().luma_worker_database_url.get_secret_value()) as saver:
        return build_graph(saver).get_state({"configurable": {"thread_id": f"{env['company']}:{cid}"}}).next


@pytest.mark.parametrize("decision", ["approve", "reject"])
def test_staff_decision_resumes_review_after_restart(environment, decision):
    """The backend's exact-revision decision resumes a persisted review in a new worker without redrafting."""
    env = environment
    cid = create_request(env)
    run_next(env, cid)
    assert pending(env, cid) == ("review",)
    quote = get_detail(env, cid)["quote"]
    assert quote["content"]["total"] == "97.05"
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": decision}
        ).status_code
        == 200
    )
    run_next(env, cid)
    assert pending(env, cid) == ()
    after = get_detail(env, cid)["quote"]
    assert after["id"] == quote["id"]
    assert after["status"] == ("approved" if decision == "approve" else "rejected")


def test_customer_clarification_resumes_after_restart(environment):
    """A missing request pauses once, then written customer fields resume extraction in another process."""
    env = environment
    created = post(
        env,
        "/conversations",
        {
            "customer_name": "Synthetic clarification",
            "customer_company": "Fixture",
            "text": "I need downlights.",
        },
    )
    assert created.status_code == 200
    cid = created.json()["id"]
    run_next(env, cid)
    assert pending(env, cid) == ("clarify",)
    assert get_detail(env, cid)["quote"] is None
    assert (
        post(env, f"/conversations/{cid}/customer-reply", {"text": "Please quote 3 DL-001."}).status_code
        == 200
    )
    run_next(env, cid)
    assert pending(env, cid) == ("review",)
    assert get_detail(env, cid)["quote"]["content"]["total"] == "97.05"


def test_manual_decision_job_cannot_start_an_agent_run(environment):
    """A review-only job for a manual quote must not start a new extraction or overwrite staff work."""
    env = environment
    cid = create_request(env)
    quote = make_draft(env, cid)
    run_next(env, cid)  # Older preparation is intentionally skipped.
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 200
    )
    run_next(env, cid)
    assert pending(env, cid) == ()
    assert get_detail(env, cid)["quote"]["id"] == quote["id"]


def test_duplicate_work_is_not_a_customer_answer(environment):
    """An extra queued job cannot resume clarification or create another identical customer question."""
    env = environment
    response = post(
        env,
        "/conversations",
        {"customer_name": "Synthetic customer", "customer_company": "Fixture", "text": "Need downlights."},
    )
    cid = response.json()["id"]
    run_next(env, cid)
    before = get_detail(env, cid)["delivery"]
    with database(worker=True) as conn:
        enqueue(conn, env["company"], cid)
    run_next(env, cid)
    assert get_detail(env, cid)["delivery"] == before
    assert pending(env, cid) == ("clarify",)


def test_voice_waits_for_processing_and_exact_written_confirmation(environment):
    """Pending media is silent; a simulated readable transcript plus 'yes' still cannot create a quotation."""
    env = environment
    cid = create_request(env)
    response = upload(env, cid, wav_bytes())
    mid = response.json()["message_id"]
    run_next(env, cid)  # Older preparation sees pending media and waits silently.
    assert pending(env, cid) == ()
    assert get_detail(env, cid)["delivery"] == []
    # Explicit fixture publication isolates graph policy from provider accuracy.
    # Real transcription has a separate opt-in canary and is not claimed here.
    with database(worker=True) as conn:
        complete_media(conn, env["company"], cid, mid, status="ready", text="Please quote 3 DL-001.")
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "update luma.jobs set status='done' where company_id=%s and kind='transcribe'", (env["company"],)
        )
    run_next(env, cid)
    assert pending(env, cid) == ("clarify",)
    assert get_detail(env, cid)["quote"] is None
    assert post(env, f"/conversations/{cid}/customer-reply", {"text": "yes"}).status_code == 200
    run_next(env, cid)
    assert get_detail(env, cid)["quote"] is None
    assert post(env, f"/conversations/{cid}/customer-reply", {"text": "Confirm 3 DL-001."}).status_code == 200
    run_next(env, cid)
    assert pending(env, cid) == ("review",)
    assert get_detail(env, cid)["quote"]["content"]["total"] == "97.05"


def test_descriptive_request_gets_cited_choices_before_selection(environment):
    """Catalog matches help an unknown-SKU customer choose; similarity never silently creates a final line."""
    env = environment
    response = post(
        env,
        "/conversations",
        {
            "customer_name": "Synthetic customer",
            "customer_company": "Fixture",
            "text": "I need downlights 18W 4000K IP44.",
        },
    )
    assert response.status_code == 200
    cid = response.json()["id"]
    run_next(env, cid)
    current = get_detail(env, cid)
    assert current["quote"] is None
    question = current["delivery"][0]["preview"]
    assert "DL-001" in question and "catalog v1, page 1" in question
    assert "not confirmed equivalents" in question and "text reply" in question
    assert (
        post(env, f"/conversations/{cid}/customer-reply", {"text": "Please quote 3 DL-001."}).status_code
        == 200
    )
    run_next(env, cid)
    assert get_detail(env, cid)["quote"]["content"]["total"] == "97.05"
