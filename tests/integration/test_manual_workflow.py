"""Actual HTTP/Auth/PostgreSQL tests for approval, revisions, isolation, and local delivery."""

from uuid import uuid4

import psycopg
from luma.core.database import database
from luma_agent.runtime.delivery import deliver_one


def post(env, path, body, key=None):
    """Submit an authenticated mutation with an explicit operation identity; never log the bearer token."""
    return env["api"].post(
        "/api" + path, headers={**env["headers"], "Idempotency-Key": str(key or uuid4())}, json=body
    )


def create_request(env):
    """Create a synthetic local request through the actual public business interface."""
    response = post(
        env,
        "/conversations",
        {
            "customer_name": "Synthetic test customer",
            "customer_company": "Fixture company",
            "text": "Please quote 3 DL-001.",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def get_detail(env, cid):
    """Fetch canonical conversation state under the current authenticated membership."""
    response = env["api"].get("/api/conversations/" + cid, headers=env["headers"])
    assert response.status_code == 200, response.text
    return response.json()


def make_draft(env, cid, quantity=3):
    """Draft using the currently observed optimistic version and a server-owned product price."""
    current = get_detail(env, cid)["conversation"]
    response = post(
        env,
        f"/conversations/{cid}/draft",
        {
            "expected_version": current["version"],
            "lines": [{"product_id": str(env["products"][0]), "quantity": quantity}],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_complete_manual_quotation_and_local_delivery(environment):
    """A real staff review produces one bound approval and an honest local-channel delivery outcome."""
    env = environment
    cid = create_request(env)
    quote = make_draft(env, cid)
    assert quote["content"]["total"] == "97.05"
    key = uuid4()
    body = {"expected_revision": 1, "decision": "approve"}
    first = post(env, f"/conversations/{cid}/decision", body, key)
    assert first.status_code == 200, first.text
    assert post(env, f"/conversations/{cid}/decision", body, key).json() == first.json()
    assert deliver_one()
    current = get_detail(env, cid)
    assert current["delivery"][0]["status"] == "local_delivered"
    assert len([m for m in current["messages"] if m["kind"] == "document"]) == 1
    assert deliver_one() is False


def test_revision_invalidates_approval_and_blocks_old_dispatch(environment):
    """A changed quantity creates another revision and prevents a previously queued quotation from sending."""
    env = environment
    cid = create_request(env)
    make_draft(env, cid)
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 200
    )
    quote = make_draft(env, cid, 4)
    assert quote["revision"] == 2 and quote["status"] == "review"
    assert get_detail(env, cid)["delivery"][0]["status"] == "blocked"
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 409
    )


def test_takeover_prevents_queued_delivery(environment):
    """Ownership changes block an already approved but not submitted automated quotation."""
    env = environment
    cid = create_request(env)
    make_draft(env, cid)
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 200
    )
    current = get_detail(env, cid)["conversation"]
    response = post(
        env, f"/conversations/{cid}/ownership", {"expected_version": current["version"], "owner": "staff"}
    )
    assert response.status_code == 200, response.text
    assert get_detail(env, cid)["delivery"][0]["status"] == "blocked"
    assert deliver_one() is False


def test_changed_idempotent_payload_conflicts(environment):
    """An operation identity can never silently replay a different customer's request payload."""
    env = environment
    key = uuid4()
    body = {"customer_name": "Fixture customer", "text": "3 DL-001"}
    assert post(env, "/conversations", body, key).status_code == 200
    assert post(env, "/conversations", {**body, "text": "30 DL-001"}, key).status_code == 409


def test_cross_company_and_undeclared_authority_are_denied(environment):
    """An actual restricted RLS connection cannot see another company, and the API rejects privilege fields."""
    env = environment
    with database(env["user"]) as conn:
        companies = conn.execute("select id from luma.companies").fetchall()
        assert [row["id"] for row in companies] == [env["company"]]
        assert conn.execute("select current_user as role").fetchone()["role"] == "luma_api"
    assert env["api"].get("/api/conversations/" + str(uuid4()), headers=env["headers"]).status_code == 404
    assert (
        post(
            env,
            "/conversations",
            {"customer_name": "Fixture", "text": "Hello", "role": "admin", "company_id": str(uuid4())},
        ).status_code
        == 422
    )
    assert env["api"].get("/api/workspace").status_code in (401, 403)


def test_revoked_membership_blocks_existing_token(environment):
    """A previously valid Supabase JWT cannot continue reading after current membership is disabled."""
    env = environment
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "update luma.memberships set active=false where user_id=%s and company_id=%s",
            (env["user"], env["company"]),
        )
    assert env["api"].get("/api/workspace", headers=env["headers"]).status_code == 403
