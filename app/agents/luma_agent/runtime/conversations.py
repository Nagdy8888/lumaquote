"""Resume durable graph work without trusting browser-supplied graph commands."""

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from langsmith import tracing_context
from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError

from ..graph import build_graph


def process_conversation(job):
    """Serialize a company's graph thread and resume only its pending authorized participation point."""
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
        with PostgresSaver.from_conn_string(settings().luma_worker_database_url.get_secret_value()) as saver:
            graph = build_graph(saver)
            with tracing_context(enabled=False):
                snapshot = graph.get_state(config)
                if snapshot.next:
                    if "clarify" in snapshot.next:
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
                            graph.invoke(
                                Command(resume={"job_id": str(job["id"])}), config, durability="sync"
                            )
                            if job["payload"].get("review_only"):
                                return
                        else:
                            raise DomainError("Quotation still awaits an authorized staff decision.")
                graph.invoke(state, config, durability="sync")
