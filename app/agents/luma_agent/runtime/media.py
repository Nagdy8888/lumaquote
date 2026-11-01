"""Shared fenced media lifecycle: decode offline, reserve, read once, publish a private unconfirmed result."""

from decimal import Decimal
from uuid import UUID

from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError
from luma.core.storage import get_file, put_file
from luma.features.media.persistence import complete_media, media_record
from luma.features.media.sandbox import process_file
from psycopg.types.json import Jsonb

from ..adapters.media_reading import read_media, validate_media_provider
from ..budget import reserve
from ..lease import assert_job


def process_media(job, kind):
    """Process one trusted fixed-kind media job and expose recoverable failure.

    Resolve message identity through persisted job scope; run_media handles the
    queued-only lifecycle and admitted provider call. On an exception, publish
    unknown state and retain reserved consumption only while this fence remains
    valid, then re-raise for worker status handling. If the lease is already lost,
    that publication can be denied and the later expiry sweep owns recovery.
    This wrapper never blindly retries an uncertain provider submission.
    """
    if kind not in ("audio", "image"):
        raise DomainError("Unsupported media kind.")
    state = {"job_id": job["id"], "fence": job["fence"]}
    mid = UUID(job["payload"]["message_id"])
    company, cid = job["company_id"], job["conversation_id"]
    try:
        return run_media(job, state, company, cid, mid, kind)
    except Exception:
        with database(worker=True) as conn:
            assert_job(conn, state)
            row = media_record(conn, company, cid, mid)
            if row["status"] in ("queued", "processing"):
                conn.execute(
                    "update luma.usage set status='unknown' where job_id=%s and operation='primary' and status='reserved'",
                    (job["id"],),
                )
                complete_media(
                    conn,
                    company,
                    cid,
                    mid,
                    status="unknown",
                    text="Media processing was interrupted. Staff review or a text reply is required.",
                    normalized_path=row["normalized_path"],
                    error_code="processing_interrupted",
                )
        raise


def run_media(job, state, company, cid, mid, kind):
    """Advance a queued record through decode, private preview and one reading attempt.

    Return without replay for any nonqueued record. Persist processing, decode
    offline and store normalized bytes before paid admission so manual preview
    can survive disabled/unavailable inference. Rejected bytes publish rejected;
    disabled/denied reading publishes needs_staff. A usable reading settles only
    this job's primary estimate and publishes unconfirmed data under a fresh
    fenced transaction. Provider/publication errors propagate to process_media;
    no returned text authorizes quantities, a quote, approval or delivery.
    """
    config = settings()
    with database(worker=True) as conn:
        assert_job(conn, state)
        row = media_record(conn, company, cid, mid)
        if row["kind"] != kind:
            raise DomainError("Media type does not match the queued operation.")
        if row["status"] != "queued":
            return
        conn.execute("update luma.media set status='processing',updated_at=now() where message_id=%s", (mid,))
    original = get_file(row["original_path"])
    try:
        metadata, normalized = process_file(kind, original or b"")
    except DomainError:
        with database(worker=True) as conn:
            assert_job(conn, state)
            complete_media(
                conn,
                company,
                cid,
                mid,
                status="rejected",
                text="This attachment could not be safely processed. Please send your request as text.",
                error_code="invalid_media",
            )
        return
    suffix, mime = ("wav", "audio/wav") if kind == "audio" else ("jpg", "image/jpeg")
    path = row["original_path"].rsplit("/", 1)[0] + f"/normalized.{suffix}"
    put_file(path, normalized, mime)
    with database(worker=True) as conn:
        assert_job(conn, state)
        conn.execute(
            "update luma.media set normalized_path=%s,metadata=%s where message_id=%s",
            (path, Jsonb(metadata), mid),
        )
    if not config.enable_paid_ai:
        text = (
            "Voice note received. Automatic transcription is disabled; staff can listen or ask for text."
            if kind == "audio"
            else "Product-label photo received. Automatic reading is disabled; staff can view it or ask for text."
        )
        with database(worker=True) as conn:
            assert_job(conn, state)
            complete_media(
                conn,
                company,
                cid,
                mid,
                status="needs_staff",
                text=text,
                normalized_path=path,
                metadata=metadata,
                error_code="paid_ai_disabled",
            )
        return
    try:
        validate_media_provider(config, kind)
        with database(worker=True) as conn:
            assert_job(conn, state)
            reserve(conn, company, job["id"])
    except DomainError:
        with database(worker=True) as conn:
            assert_job(conn, state)
            complete_media(
                conn,
                company,
                cid,
                mid,
                status="needs_staff",
                text="Automatic media reading is unavailable. Staff can review the attachment or ask for text.",
                normalized_path=path,
                metadata=metadata,
                error_code="media_not_admitted",
            )
        return
    reading = read_media(config, kind, normalized, metadata)
    if reading.estimate > Decimal(str(config.reservation)):
        raise DomainError("Observed estimated consumption needs staff reconciliation.")
    with database(worker=True) as conn:
        assert_job(conn, state)
        conn.execute(
            "update luma.usage set status='settled',estimated=%s where job_id=%s and operation='primary'",
            (reading.estimate, job["id"]),
        )
        complete_media(
            conn,
            company,
            cid,
            mid,
            status=reading.status,
            text=reading.text,
            normalized_path=path,
            metadata={**metadata, **reading.metadata},
            error_code=None if reading.status == "ready" else "unconfirmed_media",
        )
