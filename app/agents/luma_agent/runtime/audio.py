"""Bounded voice decoding and one budget-reserved English transcription attempt."""

from decimal import Decimal
from uuid import UUID

from langsmith import tracing_context
from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError
from luma.core.storage import get_file, put_file
from luma.features.media.persistence import complete_media, media_record
from luma.features.media.sandbox import process_file
from openai import OpenAI

from ..budget import reserve
from ..lease import assert_job


def _process_audio(job):
    """Normalize private audio offline, reserve before the single provider call, and publish only fenced outcomes.

    Provider timeouts remain unknown and are never blindly retried. Transcript
    text is untrusted input; downstream field confirmation remains mandatory.
    """
    state = {"job_id": job["id"], "fence": job["fence"]}
    mid = UUID(job["payload"]["message_id"])
    company, cid = job["company_id"], job["conversation_id"]
    config = settings()
    with database(worker=True) as conn:
        assert_job(conn, state)
        row = media_record(conn, company, cid, mid)
        if row["status"] != "queued":
            return
        conn.execute("update luma.media set status='processing',updated_at=now() where message_id=%s", (mid,))
    original = get_file(row["original_path"])
    try:
        metadata, normalized = process_file("audio", original or b"")
    except DomainError:
        with database(worker=True) as conn:
            assert_job(conn, state)
            complete_media(
                conn,
                company,
                cid,
                mid,
                status="rejected",
                text="This voice note could not be safely processed. Please send your request as text.",
                error_code="invalid_audio",
            )
        return
    path = row["original_path"].rsplit("/", 1)[0] + "/normalized.wav"
    put_file(path, normalized, "audio/wav")
    if not config.enable_paid_ai:
        with database(worker=True) as conn:
            assert_job(conn, state)
            complete_media(
                conn,
                company,
                cid,
                mid,
                status="needs_staff",
                normalized_path=path,
                metadata=metadata,
                text="Voice note received. Automatic transcription is disabled; staff can listen or ask for text.",
                error_code="paid_ai_disabled",
            )
        return
    try:
        if config.transcription_model != "gpt-transcribe" or not config.openai_api_key.get_secret_value():
            raise DomainError("The configured transcription model/key has not been verified.", 503)
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
                normalized_path=path,
                metadata=metadata,
                text="Automatic transcription is unavailable. Staff can listen or ask for text.",
                error_code="transcription_not_admitted",
            )
        return
    try:
        with tracing_context(enabled=False):
            response = OpenAI(
                api_key=config.openai_api_key.get_secret_value(), timeout=45, max_retries=0
            ).audio.transcriptions.create(
                model=config.transcription_model,
                file=("voice-note.wav", normalized, "audio/wav"),
                languages=["en"],
                response_format="json",
            )
        languages = [language.code for language in response.languages or []]
        text = response.text.strip()
        english = bool(languages) and all(language in ("en", "eng") for language in languages)
        if not text or len(text) > 16000 or not english:
            status, text = (
                "needs_staff",
                "This recording needs staff review. Please confirm your request in English text.",
            )
        else:
            status = "ready"
        # Duration-based estimate from the verified model price, never an invoice.
        estimate = Decimal(str(metadata["duration"])) * Decimal("0.0045") / Decimal(60)
        with database(worker=True) as conn:
            assert_job(conn, state)
            conn.execute(
                "update luma.usage set status='settled',estimated=%s where job_id=%s", (estimate, job["id"])
            )
            complete_media(
                conn,
                company,
                cid,
                mid,
                status=status,
                text=text,
                normalized_path=path,
                metadata={**metadata, "languages": languages},
                error_code=None if status == "ready" else "unconfirmed_language",
            )
    except Exception:
        with database(worker=True) as conn:
            conn.execute("update luma.usage set status='unknown' where job_id=%s", (job["id"],))
            assert_job(conn, state)
            complete_media(
                conn,
                company,
                cid,
                mid,
                status="unknown",
                text="Voice transcription outcome is uncertain. Staff review is required before retrying.",
                normalized_path=path,
                metadata=metadata,
                error_code="provider_outcome_unknown",
            )
        raise


def process_audio(job):
    """Ensure an interrupted parser/storage/provider attempt leaves a visible uncertain state when its lease is still valid.

    Infrastructure failures still propagate to the durable job outcome. A stale
    owner cannot publish a result, and unknown calls never receive an automatic
    new reservation or retry.
    """
    try:
        return _process_audio(job)
    except Exception:
        with database(worker=True) as conn:
            assert_job(conn, {"job_id": job["id"], "fence": job["fence"]})
            row = media_record(
                conn, job["company_id"], job["conversation_id"], UUID(job["payload"]["message_id"])
            )
            if row["status"] in ("queued", "processing"):
                complete_media(
                    conn,
                    job["company_id"],
                    job["conversation_id"],
                    row["message_id"],
                    status="unknown",
                    text="Voice processing was interrupted. Staff review or a text reply is required.",
                    normalized_path=row["normalized_path"],
                    error_code="processing_interrupted",
                )
        raise
