"""Private local-test media intake, independent of provider processing and HTTP."""

from uuid import uuid4

from luma.core.admission import enqueue, rate_limit
from luma.core.audit import audit
from luma.core.errors import DomainError
from luma.core.storage import put_file
from luma.features.conversations.repository import conversation
from luma.features.conversations.service import add_message
from luma.features.inventory import ledger


def authorize_upload(conn, company, cid):
    """Require an existing scoped local-test conversation; live media enters through its separately verified channel."""
    current = conversation(conn, company, cid, lock=True)
    if current["channel"] != "local_test":
        raise DomainError("Staff test uploads are only available in the local test channel.", 403)
    return current


def accept_media(conn, member, user, cid, expected_version, data, *, kind):
    """Persist one opaque private original and queue bounded media processing, invalidating earlier offers atomically.

    The caller holds the operation's idempotency lock. Storage failure rolls back
    business effects; interrupted pre-commit uploads may leave a private orphan
    for retention cleanup, never a dispatched message or approved quotation.
    """
    if kind not in ("audio", "image"):
        raise DomainError("Unsupported media kind.", 422)
    company = member["company_id"]
    current = authorize_upload(conn, company, cid)
    if current["version"] != expected_version:
        raise DomainError("The conversation changed. Review it before uploading this attachment.")
    return store_media(conn, company, user, cid, data, kind=kind)


def store_media(conn, company, actor, cid, data, *, kind, provider_id=None):
    """Store an already-authorized original, supersede affected offers and queue processing in this transaction.

    Callers establish who may attach media (a staff upload to a local-test thread or a
    verified, allow-listed WhatsApp sender) and hold the conversation lock. This applies the
    shared size bounds, the per-conversation rate limit, immutable storage, revision
    invalidation and job admission. `provider_id` deduplicates a re-delivered provider
    message: a repeat returns None without storing anything again.
    """
    label, maximum, job_kind = (
        ("Voice note", 10, "transcribe") if kind == "audio" else ("Product-label photo", 5, "read_photo")
    )
    if not data or len(data) > maximum * 1024 * 1024:
        raise DomainError(f"{label} must be nonempty and no larger than {maximum} MB.", 413)
    rate_limit(conn, f"conversation:{cid}", 6)
    path = f"{company}/media/{uuid4()}/original"
    put_file(path, data, "application/octet-stream")
    message = add_message(
        conn,
        company,
        cid,
        "customer",
        f"{label} awaiting processing.",
        kind=kind,
        object_path=path,
        provider_id=provider_id,
    )
    if message is None:
        return None
    conn.execute(
        "insert into luma.media(message_id,company_id,conversation_id,original_path,kind) values(%s,%s,%s,%s,%s)",
        (message, company, cid, path, kind),
    )
    superseded = conn.execute(
        "update luma.quotes set status='superseded' where conversation_id=%s and status in ('review','approved') returning id",
        (cid,),
    ).fetchall()
    for row in superseded:
        ledger.release_quote(conn, company, row["id"], "superseded")
    conn.execute(
        "update luma.outbox set status='blocked',error_code='customer_revision',updated_at=now() where conversation_id=%s and status='queued'",
        (cid,),
    )
    conn.execute(
        "update luma.conversations set last_customer_at=now(),status='processing_media' where id=%s", (cid,)
    )
    enqueue(conn, company, cid, kind=job_kind, payload={"message_id": str(message)})
    audit(conn, company, actor, f"media.{kind}_received", message)
    return {"message_id": str(message), "status": "queued"}


def accept_audio(conn, member, user, cid, expected_version, data):
    """Preserve the voice intake interface while sharing immutable original, revision invalidation and job admission with photos."""
    return accept_media(conn, member, user, cid, expected_version, data, kind="audio")
