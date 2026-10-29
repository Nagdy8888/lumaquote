"""Queued preparation cannot undo human work or act on a stale extracted request."""

import psycopg
import pytest
from luma.core.errors import DomainError
from luma_agent.nodes.workflow import ask, prepare
from luma_agent.runtime.conversations import process_conversation
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail, make_draft, post


def running_job(env, cid):
    """Give this fixture's own queued job a valid real database lease for business-node regression checks."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        return conn.execute(
            """update luma.jobs set status='running',fence=1,lease_until=now()+interval '120 seconds'
            where company_id=%s and conversation_id=%s returning *""",
            (env["company"], cid),
        ).fetchone()


@pytest.mark.parametrize("decision", [None, "approve", "reject"])
def test_older_preparation_preserves_staff_revision(environment, decision):
    """A job queued before manual drafting cannot create another revision after staff review, approval, or rejection."""
    env = environment
    cid = create_request(env)
    quote = make_draft(env, cid)
    if decision:
        assert (
            post(
                env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": decision}
            ).status_code
            == 200
        )
    before = get_detail(env, cid)
    process_conversation(running_job(env, cid))
    after = get_detail(env, cid)
    assert after["quote"]["id"] == quote["id"]
    assert after["quote"]["status"] == before["quote"]["status"]
    assert after["conversation"]["version"] == before["conversation"]["version"]


@pytest.mark.parametrize("node", [ask, prepare])
def test_stale_extraction_cannot_ask_or_replace_draft(environment, node):
    """Late extraction must fail before creating an obsolete clarification or overwriting a newer staff draft."""
    env = environment
    cid = create_request(env)
    original = get_detail(env, cid)["conversation"]["version"]
    quote = make_draft(env, cid)
    job = running_job(env, cid)
    state = {
        "company_id": str(env["company"]),
        "conversation_id": cid,
        "job_id": str(job["id"]),
        "fence": job["fence"],
        "observed_version": original,
        "clarification": "Which quantity?",
        "extraction": {"lines": [{"sku": "DL-001", "quantity": 30}]},
    }
    with pytest.raises(DomainError):
        node(state)
    after = get_detail(env, cid)
    assert after["quote"]["id"] == quote["id"]
    assert after["quote"]["content"]["lines"][0]["quantity"] == 3
    assert not after["delivery"]
