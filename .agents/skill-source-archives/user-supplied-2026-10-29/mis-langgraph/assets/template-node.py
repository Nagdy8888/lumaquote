"""Triage node for the <agent_name> graph.

Classifies the most recent inbound message into one of the ``TriageKind``
discriminators. The decision is read by ``route_after_triage`` to pick the
next branch — this node performs no I/O of its own beyond the LLM call.
"""
from __future__ import annotations

from langchain_core.runnables import RunnableConfig

from <agent_name>.prompts.triage import TRIAGE_PROMPT
from <agent_name>.schemas.states import AgentState, TriageKind
from <agent_name>.utils import call_structured_llm


async def triage_email(state: AgentState, config: RunnableConfig) -> dict:
    """Decide whether to respond, ignore, or notify on the inbound email.

    Args:
        state: current graph state — uses the last entry of ``messages``.
        config: per-run config — reads ``configurable.tenant_id`` for the prompt.

    Returns:
        ``{"triage_decision": <TriageKind>}`` to merge into state.

    Raises:
        ValueError: if the LLM returns an unrecognised kind.
    """
    last_message = state["messages"][-1]
    tenant_id = config["configurable"]["tenant_id"]

    decision = await call_structured_llm(
        prompt=TRIAGE_PROMPT,
        message=last_message,
        tenant_id=tenant_id,
    )

    if decision.kind not in ("respond", "ignore", "notify"):
        raise ValueError(f"unrecognised triage kind: {decision.kind!r}")

    return {"triage_decision": decision.kind}
