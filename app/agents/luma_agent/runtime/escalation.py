"""Give staff a signal when an agent job ends without answering the customer."""

from luma.core.audit import audit
from luma.core.database import database
from luma.features.conversations.service import add_message


def escalate_unanswered(job, failure: str) -> bool:
    """Mark the conversation `needs_staff` when a failed agent job left the latest customer message unhandled.

    Purpose: a job that raises (a business `DomainError` such as a refused draft, or any other
    error) is not retried, so without this the customer would get no reply and staff no signal.
    Acts only when the conversation is still agent-owned, its status is `new` (set by every
    customer text, so no reply or draft has been made for it) and no customer message arrived
    after the job was created (that message has its own job). Then it appends one system
    message naming only the opaque failure class and sets `needs_staff`. Staff-owned, reviewing,
    clarifying or already escalated conversations are untouched, so a repeated failure adds
    nothing. Audit `job.escalated`. Runs in its own short worker transaction, locks the
    conversation row, never sends a customer message and never calls a model. Returns True
    when it escalated.
    """
    with database(worker=True) as conn:
        row = conn.execute(
            """select owner,status,last_customer_at from luma.conversations
            where id=%s and company_id=%s for update""",
            (job["conversation_id"], job["company_id"]),
        ).fetchone()
        if not row or row["owner"] != "agent" or row["status"] != "new" or row["last_customer_at"] > job["created_at"]:
            return False
        add_message(
            conn,
            job["company_id"],
            job["conversation_id"],
            "system",
            f"Automation could not process the latest customer message ({failure}). Staff should review and reply.",
        )
        conn.execute("update luma.conversations set status='needs_staff' where id=%s", (job["conversation_id"],))
        audit(conn, job["company_id"], "worker", "job.escalated", job["id"], failure=failure)
        return True
