"""Graph builder for the <agent_name> agent.

All wiring lives here. Nodes and routing functions are imported from
``<agent_name>.nodes``; the only edge definitions in the codebase are the
``add_edge`` / ``add_conditional_edges`` calls below.
"""
from __future__ import annotations

import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from <agent_name>.nodes import (
    agent_step,
    draft_reply,
    notify_user,
    run_tools,
    triage_email,
)
from <agent_name>.nodes.routing import route_after_agent, route_after_triage
from <agent_name>.schemas.states import AgentState


def _pick_checkpointer():
    """Pick a checkpointer based on ``MIS_CHECKPOINTER`` (memory|sqlite|postgres)."""
    kind = os.environ.get("MIS_CHECKPOINTER", "memory")
    if kind == "memory":
        return MemorySaver()
    if kind == "sqlite":
        from langgraph.checkpoint.sqlite import SqliteSaver
        return SqliteSaver.from_conn_string(os.environ["MIS_SQLITE_PATH"])
    if kind == "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver
        return PostgresSaver.from_conn_string(os.environ["MIS_POSTGRES_DSN"])
    raise ValueError(f"unknown checkpointer kind: {kind!r}")


def build_graph():
    """Build and compile the <agent_name> graph.

    Topology:
        triage  --respond-->  agent  --tools-->  tools --> agent ... -> END
                |--notify-->  notify --> END
                \\--ignore--> END

    Returns:
        A compiled ``StateGraph`` ready for ``ainvoke`` / ``astream``.
    """
    g: StateGraph = StateGraph(AgentState)

    g.add_node("triage", triage_email)
    g.add_node("agent",  agent_step)
    g.add_node("tools",  run_tools)
    g.add_node("draft",  draft_reply)
    g.add_node("notify", notify_user)

    g.set_entry_point("triage")
    g.add_conditional_edges(
        "triage",
        route_after_triage,
        {"draft": "draft", "notify": "notify", "__end__": END},
    )
    g.add_edge("draft", "agent")
    g.add_conditional_edges(
        "agent",
        route_after_agent,
        {"tools": "tools", "__end__": END},
    )
    g.add_edge("tools", "agent")
    g.add_edge("notify", END)

    return g.compile(checkpointer=_pick_checkpointer())
