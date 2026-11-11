"""Resume durable graph work without trusting browser-supplied graph commands."""

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation
from luma.features.orders.service import hold_for_pending_order
from luma.features.quotations.repository import latest_quote

from ..graph import build_graph
from ..observability import masked_or_off


def process_conversation(job):
    """Run one trusted job against its company/conversation PostgreSQL thread.

    A session advisory lock spans checkpoint commits. Pending media, duplicate
    customer turns and older work already covered by staff/decided quotes return
    without new extraction. Review-only jobs can complete only an existing review
    pause; customer clarification resumes only on a new customer message. A request whose
    conversation has an accepted quotation with a still-pending order is parked (needs_staff, one
    fixed notice) before the graph runs, so no model call is made. Resume
    commands carry job identity, never approval authority. Persist checkpoints
    synchronously with bounded recursion. Graph steps are traced only inside the
    worker's masked job trace (`observability.job_trace`); otherwise tracing is off. Node/business
    errors propagate to worker outcome handling; this function does not dispatch.
    """
    state = {
        "company_id": str(job["company_id"]),
        "conversation_id": str(job["conversation_id"]),
        "job_id": str(job["id"]),
        "fence": job["fence"],
    }
    thread = f"{job['company_id']}:{job['conversation_id']}"
    config = {"configurable": {"thread_id": thread}, "recursion_limit": 20}
    with database(worker=True) as lock:
        # Session lock spans graph commits; released on connection close/crash.
        lock.execute("select pg_advisory_lock(hashtextextended(%s,0))", (thread,))
        lock.commit()
        current = conversation(lock, job["company_id"], job["conversation_id"])
        active = latest_quote(lock, job["company_id"], job["conversation_id"])
        customer = lock.execute(
            """select m.id,a.status as media_status from luma.messages m
            left join luma.media a on a.message_id=m.id and a.company_id=m.company_id
            where m.company_id=%s and m.conversation_id=%s and m.actor='customer'
            order by m.created_at desc,m.id desc limit 1""",
            (job["company_id"], job["conversation_id"]),
        ).fetchone()
        if customer and customer["media_status"] in ("queued", "processing"):
            # Do not ask about a placeholder while its durable transcript job is pending.
            return
        if (
            active
            and active["status"] not in ("superseded", "expired")
            and current["last_customer_at"] <= active["created_at"]
            and not job["payload"].get("review_only")
        ):
            # A queued older preparation must not replace a staff-prepared or
            # already approved/rejected revision, or incur another model call.
            return
        if not job["payload"].get("review_only") and current["owner"] == "agent":
            with database(worker=True) as conn:
                locked = conversation(conn, job["company_id"], job["conversation_id"], lock=True)
                if hold_for_pending_order(conn, job["company_id"], locked):
                    # Voice and photo requests reach the agent only after transcription, past the
                    # text-path check: park them here, before any extraction or paid model call.
                    return
        with (
            PostgresSaver.from_conn_string(settings().luma_worker_database_url.get_secret_value()) as saver,
            masked_or_off(),
        ):
            graph = build_graph(saver)
            snapshot = graph.get_state(config)
            if job["payload"].get("review_only") and "review" not in snapshot.next:
                # A decision job only completes an existing review interrupt.
                # It must never initiate extraction or answer a customer pause.
                return
            if snapshot.next:
                if "clarify" in snapshot.next:
                    if customer and str(customer["id"]) == snapshot.values.get("customer_message_id"):
                        # Duplicate queued work is not a new customer answer.
                        return
                    graph.invoke(
                        Command(resume={"job_id": str(job["id"]), "fence": job["fence"]}),
                        config,
                        durability="sync",
                    )
                    return
                if "review" in snapshot.next:
                    with database(worker=True) as conn:
                        quote = conn.execute(
                            "select status from luma.quotes where id=%s and company_id=%s",
                            (snapshot.values.get("quote_id"), job["company_id"]),
                        ).fetchone()
                    if quote and quote["status"] in ("approved", "rejected", "superseded", "expired"):
                        graph.invoke(Command(resume={"job_id": str(job["id"])}), config, durability="sync")
                        if job["payload"].get("review_only"):
                            return
                    else:
                        raise DomainError("Quotation still awaits an authorized staff decision.")
            graph.invoke(state, config, durability="sync")
