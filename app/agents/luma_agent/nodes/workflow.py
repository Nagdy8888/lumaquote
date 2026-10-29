from uuid import uuid4

from langgraph.types import Command, interrupt
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation
from luma.features.conversations.service import add_message
from luma.features.quotations.drafting import draft as create_draft
from luma.features.quotations.schemas import DraftInput, Selection
from psycopg.types.json import Jsonb

from ..lease import assert_job, assert_request_version


def ask(state):
    """Persist one scoped clarification intent; interrupted-node replay never runs this node again."""
    question = state["clarification"]
    with database(worker=True) as conn:
        assert_job(conn, state)
        current = conversation(conn, state["company_id"], state["conversation_id"], lock=True)
        if current["owner"] != "agent":
            raise DomainError("Automation paused.")
        assert_request_version(current, state)
        conn.execute(
            """insert into luma.outbox(id,company_id,conversation_id,kind,payload,action_key)
            values(%s,%s,%s,'reply',%s,%s) on conflict(action_key) do nothing""",
            (
                uuid4(),
                state["company_id"],
                state["conversation_id"],
                Jsonb({"text": question}),
                f"clarify:{state['job_id']}",
            ),
        )
        conn.execute(
            "update luma.conversations set status='clarifying' where id=%s", (state["conversation_id"],)
        )
    return {}


def clarify(state):
    """Wait durably for a customer response and resume extraction with the current worker lease."""
    answer = interrupt({"kind": "customer_clarification", "question": state["clarification"]})
    # API authorization and ownership precede resume. Only opaque job identity
    # enters the graph; it is not customer-supplied authority.
    return Command(update={"job_id": answer["job_id"], "fence": answer["fence"]}, goto="extract")


def prepare(state):
    """Match explicit SKUs to authoritative records and create a staff-review draft; unsupported requests escalate."""
    with database(worker=True) as conn:
        assert_job(conn, state)
        current = conversation(conn, state["company_id"], state["conversation_id"], lock=True)
        if current["owner"] != "agent":
            raise DomainError("Automation paused.")
        assert_request_version(current, state)
        selections = []
        for line in state["extraction"]["lines"]:
            p = conn.execute(
                "select * from luma.products where company_id=%s and sku=%s",
                (state["company_id"], line["sku"].upper()),
            ).fetchone()
            if not p or p["discontinued"] or p["available"] < line["quantity"]:
                add_message(
                    conn,
                    state["company_id"],
                    state["conversation_id"],
                    "system",
                    "A requested model or quantity needs staff review. No unsupported substitute was selected.",
                )
                conn.execute(
                    "update luma.conversations set status='needs_staff' where id=%s", (current["id"],)
                )
                return {"quote_id": None}
            selections.append(Selection(product_id=p["id"], quantity=line["quantity"]))
        quote = create_draft(
            conn,
            {"company_id": state["company_id"], "role": "salesperson"},
            "agent",
            current["id"],
            DraftInput(expected_version=current["version"], lines=selections),
        )
        add_message(
            conn,
            state["company_id"],
            current["id"],
            "system",
            "Quotation prepared from catalog evidence and the current commercial snapshot. Staff approval is required.",
        )
        return {"quote_id": str(quote["id"])}


def review(state):
    """Pause for staff participation and validate the persisted decision; a resume value cannot approve a quote."""
    if not state.get("quote_id"):
        return {}
    decision = interrupt({"kind": "staff_review", "quote_id": state["quote_id"]})
    # A resume value cannot approve anything: confirm the persisted staff decision.
    with database(worker=True) as conn:
        quote = conn.execute(
            "select status from luma.quotes where company_id=%s and id=%s",
            (state["company_id"], state["quote_id"]),
        ).fetchone()
        if not quote or quote["status"] not in ("approved", "rejected", "superseded", "expired"):
            raise DomainError("A persisted staff decision is required before graph completion.")
    return {"job_id": decision.get("job_id", state["job_id"])}
