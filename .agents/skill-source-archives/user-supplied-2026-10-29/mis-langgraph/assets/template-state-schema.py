"""State and routing types for the <agent_name> graph.

Defines the TypedDict state passed between nodes, the discriminator types
used by routing functions, and any per-step intermediate shapes.
"""
from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

# ---------------------------------------------------------------------------
# Routing discriminators
# ---------------------------------------------------------------------------

TriageKind = Literal["respond", "ignore", "notify"]
"""Discrete triage outcomes used by ``route_after_triage``."""


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """Working state for the <agent_name> graph.

    Keep this lean: only fields that nodes read or update. Large artefacts
    (full email bodies, document content) go in the virtual filesystem or
    external storage; this state holds references.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    """Conversation messages; ``add_messages`` reducer handles ids + dedup."""

    triage_decision: TriageKind | None
    """Outcome of the triage node; read by ``route_after_triage``."""

    inbound_email_id: str
    """The id of the email being handled."""

    draft: str | None
    """Drafted reply, populated by the draft node."""
