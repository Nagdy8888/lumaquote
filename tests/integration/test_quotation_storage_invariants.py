"""Database invariants hold for both restricted runtime writers, not only HTTP validation."""

from uuid import uuid4

import psycopg
import pytest
from luma.core.database import database
from psycopg.types.json import Jsonb
from test_manual_workflow import create_request, get_detail, make_draft


@pytest.mark.parametrize("worker", [False, True])
def test_runtime_role_cannot_rewrite_canonical_quotation(environment, worker):
    """API and worker identities must create a revision instead of changing an existing quote hash or monetary content."""
    env = environment
    cid = create_request(env)
    quote = make_draft(env, cid)
    with database(None if worker else env["user"], worker=worker) as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("update luma.quotes set content_hash=repeat('0',64) where id=%s", (quote["id"],))
    assert get_detail(env, cid)["quote"]["content"]["total"] == "97.05"


def test_quotation_dispatch_requires_an_actual_revision_identity(environment):
    """No runtime writer can enqueue a quotation document without the canonical quote that must be approved."""
    env = environment
    cid = create_request(env)
    with database(env["user"]) as conn:
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                """insert into luma.outbox(id,company_id,conversation_id,kind,payload,action_key)
                values(%s,%s,%s,'quotation',%s,%s)""",
                (uuid4(), env["company"], cid, Jsonb({"revision": 1}), str(uuid4())),
            )
