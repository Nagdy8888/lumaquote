import json

from psycopg.types.json import Jsonb

from .contracts import digest
from .errors import DomainError


def operation(conn, member, user, action, key, payload, callback):
    """Serialize a principal-scoped idempotent mutation, reject changed payloads, and replay its stored response."""
    scope = f"{member['company_id']}:{user}:{action}:{key}"
    conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (scope,))
    previous = conn.execute(
        """select * from luma.operations
        where company_id=%s and user_id=%s and action=%s and key=%s""",
        (member["company_id"], user, action, key),
    ).fetchone()
    fingerprint = digest(payload)
    if previous:
        if previous["digest"] != fingerprint:
            raise DomainError("This operation identity was already used with different input.")
        return previous["response"]
    result = callback()
    # Persist only serializable canonical responses, so replay matches the initial response.
    response = json.loads(json.dumps(result, default=str))
    conn.execute(
        """insert into luma.operations(company_id,user_id,action,key,digest,response)
        values(%s,%s,%s,%s,%s,%s)""",
        (member["company_id"], user, action, key, fingerprint, Jsonb(response)),
    )
    return response
