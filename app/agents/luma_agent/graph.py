from typing import Literal

from langgraph.graph import END, START, StateGraph

from .nodes.extraction import extract
from .nodes.retrieval import retrieve
from .nodes.workflow import ask, clarify, prepare, review
from .state import AgentState


def route(state) -> Literal["ask", "prepare"]:
    """Choose clarification when extraction cannot safely support a quotation."""
    return "ask" if state.get("clarification") else "prepare"


def build_graph(checkpointer):
    """Compile the single explicit workflow with the supplied durable checkpointer; no channel send occurs inside nodes."""
    return (
        StateGraph(AgentState)
        .add_node("extract", extract)
        .add_node("retrieve", retrieve)
        .add_node("ask", ask)
        .add_node("clarify", clarify)
        .add_node("prepare", prepare)
        .add_node("review", review)
        .add_edge(START, "extract")
        .add_edge("extract", "retrieve")
        .add_conditional_edges("retrieve", route)
        .add_edge("ask", "clarify")
        .add_edge("prepare", "review")
        .add_edge("review", END)
        .compile(checkpointer=checkpointer)
    )
