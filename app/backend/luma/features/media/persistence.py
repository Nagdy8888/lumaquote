"""Scoped media lifecycle and transcript publication owned by the backend feature."""

from psycopg.types.json import Jsonb

from luma.core.admission import enqueue
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation


def media_record(conn, company, cid, mid):
    """Resolve a worker-selected media message through both tenant and conversation boundaries."""
    row = conn.execute(
        "select * from luma.media where company_id=%s and conversation_id=%s and message_id=%s",
        (company, cid, mid),
    ).fetchone()
    if not row:
        raise DomainError("Attachment not found.", 404)
    return row


def complete_media(
    conn, company, cid, mid, *, status, text, normalized_path=None, metadata=None, error_code=None
):
    """Publish a linked voice transcript, label reading or failure without confirming fields or granting outbound authority.

    A transcript superseded by a newer customer reply cannot overwrite its request
    status. Staff ownership still permits internal transcription, but suppresses
    automatic graph admission.
    """
    current = conversation(conn, company, cid, lock=True)
    row = media_record(conn, company, cid, mid)
    conn.execute(
        """update luma.media set status=%s,transcript=%s,normalized_path=%s,metadata=%s,
        error_code=%s,updated_at=now() where message_id=%s and company_id=%s""",
        (
            status,
            text if status == "ready" else None,
            normalized_path,
            Jsonb(metadata or {}),
            error_code,
            mid,
            company,
        ),
    )
    conn.execute("update luma.messages set body=%s where id=%s and company_id=%s", (text, mid, company))
    conn.execute("update luma.conversations set version=version+1,updated_at=now() where id=%s", (cid,))
    if current["last_customer_at"] <= row["created_at"]:
        conn.execute(
            "update luma.conversations set status=%s where id=%s",
            ("new" if status == "ready" and current["owner"] == "agent" else "needs_staff", cid),
        )
    if status == "ready" and current["owner"] == "agent":
        enqueue(conn, company, cid)
