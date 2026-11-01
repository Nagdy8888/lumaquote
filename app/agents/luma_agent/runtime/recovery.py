"""Bounded recovery of expired jobs without replaying uncertain provider operations."""

from luma.core.audit import audit
from luma.features.conversations.service import add_message
from luma.features.media.persistence import complete_media, media_record


def recover_expired(conn, company=None):
    """Fence up to 100 expired jobs and expose manual recovery, retaining all uncertain consumption.

    The optional company scope is for trusted local verification, never client
    authority. Locked active transactions are skipped. This does not retry work,
    release reservations, approve quotations or create outbound messages.
    """
    jobs = conn.execute(
        """select * from luma.jobs where status='running' and lease_until<now()
        and (%s::uuid is null or company_id=%s)
        order by created_at for update skip locked limit 100""",
        (company, company),
    ).fetchall()
    for job in jobs:
        conn.execute(
            """update luma.jobs set status='failed',error_code='worker_interrupted',
            fence=fence+1,lease_until=null where id=%s""",
            (job["id"],),
        )
        conn.execute(
            "update luma.usage set status='unknown' where job_id=%s and status='reserved'",
            (job["id"],),
        )
        if job["kind"] in ("transcribe", "read_photo"):
            mid = job["payload"]["message_id"]
            row = media_record(conn, job["company_id"], job["conversation_id"], mid)
            if row["status"] in ("queued", "processing"):
                complete_media(
                    conn,
                    job["company_id"],
                    job["conversation_id"],
                    mid,
                    status="unknown",
                    text="Attachment processing was interrupted. Staff review or a text reply is required.",
                    normalized_path=row["normalized_path"],
                    metadata=row["metadata"],
                    error_code="worker_interrupted",
                )
        else:
            add_message(
                conn,
                job["company_id"],
                job["conversation_id"],
                "system",
                "Automation was interrupted. Staff should review this request before continuing; uncertain provider work was not retried.",
            )
            conn.execute(
                """update luma.conversations set status='needs_staff'
                where id=%s and company_id=%s and last_customer_at<=%s
                and status in ('new','clarifying','processing_media')""",
                (job["conversation_id"], job["company_id"], job["created_at"]),
            )
        audit(conn, job["company_id"], "worker", "job.interrupted", job["id"], kind=job["kind"])
    return len(jobs)
