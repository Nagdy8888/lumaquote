"""Concurrent PostgreSQL proof for revision conflicts and takeover/dispatch lock ordering."""

import threading
from concurrent.futures import ThreadPoolExecutor

from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.participation import change_ownership
from luma.features.conversations.repository import conversation
from luma.features.conversations.schemas import Ownership
from luma.features.quotations.drafting import draft
from luma.features.quotations.schemas import DraftInput, Selection
from luma_agent.runtime import delivery
from test_manual_workflow import create_request, get_detail, make_draft, post


def test_concurrent_edits_allow_only_one_observed_version(environment):
    """Two independent RLS connections editing the same initial version produce one revision and one explicit conflict."""
    env = environment
    cid = create_request(env)
    version = get_detail(env, cid)["conversation"]["version"]
    barrier = threading.Barrier(2)

    def save(quantity):
        """Race one real transaction against the other editor using the same observed precondition."""
        try:
            with database(env["user"]) as conn:
                barrier.wait(timeout=5)
                result = draft(
                    conn,
                    {"company_id": env["company"], "role": "admin"},
                    env["user"],
                    cid,
                    DraftInput(
                        expected_version=version,
                        lines=[Selection(product_id=env["products"][0], quantity=quantity)],
                    ),
                )
                return result["revision"]
        except DomainError as error:
            return error.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, [3, 4]))
    assert sorted(results) == [1, 409]
    assert get_detail(env, cid)["quote"]["revision"] == 1


def test_takeover_and_dispatch_use_one_lock_order(environment, monkeypatch):
    """A dispatcher waiting on human ownership cannot hold the outbox lock and deadlock takeover."""
    env = environment
    cid = create_request(env)
    make_draft(env, cid)
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 200
    )
    reached = threading.Event()
    original = delivery.conversation

    def signal_before_conversation_lock(*args, **kwargs):
        """Expose a deterministic scheduling barrier while still acquiring the actual PostgreSQL row lock."""
        reached.set()
        return original(*args, **kwargs)

    monkeypatch.setattr(delivery, "conversation", signal_before_conversation_lock)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with database(env["user"]) as conn:
            current = conversation(conn, env["company"], cid, lock=True)
            future = pool.submit(delivery.deliver_one, env["company"])
            assert reached.wait(5)
            result = change_ownership(
                conn,
                {"company_id": env["company"]},
                env["user"],
                cid,
                Ownership(expected_version=current["version"], owner="staff"),
            )
            assert result["conversation"]["owner"] == "staff"
        assert future.result(timeout=5) is False
    state = get_detail(env, cid)
    assert state["delivery"][0]["status"] == "blocked"
    assert not any(message["kind"] == "document" for message in state["messages"])


def test_customer_revision_and_rejection_have_truthful_request_status(environment):
    """The inbox cannot retain a needs-approval state after that approval is rejected or superseded by customer input."""
    env = environment
    cid = create_request(env)
    make_draft(env, cid)
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "reject"}
        ).status_code
        == 200
    )
    assert get_detail(env, cid)["conversation"]["status"] == "needs_staff"
    quote = make_draft(env, cid, 4)
    assert (
        post(
            env,
            f"/conversations/{cid}/decision",
            {"expected_revision": quote["revision"], "decision": "approve"},
        ).status_code
        == 200
    )
    assert get_detail(env, cid)["conversation"]["status"] == "delivery_queued"
    response = post(
        env, f"/conversations/{cid}/customer-reply", {"text": "Please change the quantity to five DL-001."}
    )
    assert response.status_code == 200, response.text
    state = get_detail(env, cid)
    assert state["conversation"]["status"] == "new"
    assert state["quote"]["status"] == "superseded"
    assert state["delivery"][0]["status"] == "blocked"
