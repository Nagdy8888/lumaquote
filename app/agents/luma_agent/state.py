from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Compact persisted graph references and extraction state; secrets, full files, and approval authority stay elsewhere."""

    company_id: str
    conversation_id: str
    job_id: str
    fence: int
    extraction: dict
    clarification: str | None
    quote_id: str | None
