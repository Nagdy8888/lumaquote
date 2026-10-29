"""Private local-test voice intake, independent of provider processing and HTTP."""

from uuid import uuid4

from luma.core.admission import enqueue, rate_limit
from luma.core.audit import audit
from luma.core.errors import DomainError
from luma.core.storage import put_file
from luma.features.conversations.repository import conversation
from luma.features.conversations.service import add_message


def authorize_upload(conn, company, cid):
    """Require an existing scoped local-test conversation; live media enters through its separately verified channel."""
    current = conversation(conn, company, cid, lock=True)
    if current["channel"] != "local_test":
        raise DomainError("Staff test uploads are only available in the local test channel.", 403)
    return current


def accept_audio(conn, member, user, cid, expected_version, data):
    """Persist one opaque private original and queue bounded transcription, invalidating earlier offers atomically.

    The caller holds the operation's idempotency lock. Storage failure rolls back
    business effects; interrupted pre-commit uploads may leave a private orphan
    for retention cleanup, never a dispatched message or approved quotation.
    """
    company = member["company_id"]
    current = authorize_upload(conn, company, cid)
    if current["version"] != expected_version:
        raise DomainError("The conversation changed. Review it before uploading this voice note.")
    if not data or len(data) > 10 * 1024 * 1024:
        raise DomainError("Voice notes must be nonempty and no larger than 10 MB.", 413)
    rate_limit(conn, f"conversation:{cid}", 6)
    path = f"{company}/media/{uuid4()}/original"
    put_file(path, data, "application/octet-stream")
    message = add_message(
        conn, company, cid, "customer", "Voice note awaiting processing.", kind="audio", object_path=path
    )
    conn.execute(
        "insert into luma.media(message_id,company_id,conversation_id,original_path) values(%s,%s,%s,%s)",
        (message, company, cid, path),
    )
    conn.execute(
        "update luma.quotes set status='superseded' where conversation_id=%s and status in ('review','approved')",
        (cid,),
    )
    conn.execute(
        "update luma.outbox set status='blocked',error_code='customer_revision',updated_at=now() where conversation_id=%s and status='queued'",
        (cid,),
    )
    conn.execute(
        "update luma.conversations set last_customer_at=now(),status='processing_media' where id=%s", (cid,)
    )
    enqueue(conn, company, cid, kind="transcribe", payload={"message_id": str(message)})
    audit(conn, company, user, "media.audio_received", message)
    return {"message_id": str(message), "status": "queued"}
