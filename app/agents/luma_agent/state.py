from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Persist partial per-thread orchestration state, never approval credentials.

    Company/conversation/job/fence values come from a trusted worker job. The
    observed version and customer message identity bind results to their input
    turn. Extraction/questions/candidates are content-bearing persisted data and
    need access/retention controls; private files and secrets are not copied here.
    Candidate lists are replaced per turn, not accumulated. quote_id references
    a backend revision whose persisted decision must still be checked separately.
    """

    company_id: str
    conversation_id: str
    job_id: str
    fence: int
    customer_message_id: str
    observed_version: int
    extraction: dict
    clarification: str | None
    quote_id: str | None
    catalog_candidates: list[dict]
    retrieval_status: str
