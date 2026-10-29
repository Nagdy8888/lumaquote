"""Human takeover permits authorized replies without restoring paused automation."""

from uuid import uuid4

import psycopg
from luma_agent.runtime.delivery import deliver_one
from test_manual_workflow import create_request, get_detail, post


def take_over(env, cid):
    """Take ownership using the currently observed version through the actual authenticated route."""
    current = get_detail(env, cid)["conversation"]
    response = post(
        env, f"/conversations/{cid}/ownership", {"expected_version": current["version"], "owner": "staff"}
    )
    assert response.status_code == 200, response.text


def queue_reply(env, cid, key=None):
    """Queue a human clarification with a valid optimistic precondition and stable operation identity."""
    current = get_detail(env, cid)["conversation"]
    body = {
        "expected_version": current["version"],
        "text": "Could you confirm the required color temperature?",
    }
    return post(env, f"/conversations/{cid}/reply", body, key), body


def test_human_reply_requires_takeover_and_remains_distinct_from_notes(environment):
    """Only an explicit staff-owned reply reaches the customer channel; internal notes never create outbound intent."""
    env = environment
    cid = create_request(env)
    response, _ = queue_reply(env, cid)
    assert response.status_code == 409
    assert (
        post(env, f"/conversations/{cid}/messages", {"text": "Internal commercial review only."}).status_code
        == 200
    )
    take_over(env, cid)
    key = uuid4()
    response, body = queue_reply(env, cid, key)
    assert response.status_code == 200, response.text
    replay = post(env, f"/conversations/{cid}/reply", body, key)
    assert replay.status_code == 200
    assert replay.json() == response.json()
    assert deliver_one(env["company"])
    state = get_detail(env, cid)
    notes = [message for message in state["messages"] if message["actor"] == "staff"]
    assert len(notes) == 2
    assert notes[0]["outbound"] is False
    assert notes[1]["outbound"] is True
    assert state["conversation"]["owner"] == "staff"
    assert state["delivery"][0]["status"] == "local_delivered"
    assert deliver_one(env["company"]) is False


def test_resuming_automation_cancels_unsent_human_reply(environment):
    """Returning ownership to the agent cannot unexpectedly dispatch a human reply left queued earlier."""
    env = environment
    cid = create_request(env)
    take_over(env, cid)
    assert queue_reply(env, cid)[0].status_code == 200
    current = get_detail(env, cid)["conversation"]
    assert (
        post(
            env, f"/conversations/{cid}/ownership", {"expected_version": current["version"], "owner": "agent"}
        ).status_code
        == 200
    )
    assert get_detail(env, cid)["delivery"][0]["status"] == "blocked"
    assert deliver_one(env["company"]) is False


def test_reply_author_revocation_is_checked_at_dispatch(environment):
    """Revoking staff access after queueing prevents customer delivery even when the original API request was authorized."""
    env = environment
    cid = create_request(env)
    take_over(env, cid)
    assert queue_reply(env, cid)[0].status_code == 200
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "update luma.memberships set active=false where user_id=%s and company_id=%s",
            (env["user"], env["company"]),
        )
    assert deliver_one(env["company"])
    with psycopg.connect(env["dsn"]) as conn:
        assert (
            conn.execute("select status from luma.outbox where company_id=%s", (env["company"],)).fetchone()[
                0
            ]
            == "blocked"
        )
        assert (
            conn.execute(
                "select count(*) from luma.messages where company_id=%s and actor='staff' and provider_id is not null",
                (env["company"],),
            ).fetchone()[0]
            == 0
        )
