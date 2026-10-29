from psycopg.types.json import Jsonb


def audit(conn, company: str, actor: str, action: str, resource=None, **detail):
    """Append a scoped business audit event in the current transaction; detail must contain no secrets."""
    conn.execute(
        "insert into luma.audit(company_id,actor,action,resource_id,detail) values(%s,%s,%s,%s,%s)",
        (company, actor, action, resource, Jsonb(detail)),
    )
