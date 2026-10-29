"""Deep agent entry point for the <agent_name> agent.

Composes the deepagents harness with this agent's tools, permissions,
interrupts, and memory. The compiled graph is exported as ``graph`` and
referenced by ``langgraph.json``.

Run-mode flags:
    dev_mode: skip approval / interrupt gating for fast iteration.
"""
from __future__ import annotations

from deepagents import FileSystemPermission, create_deep_agent

from <agent_name>.prompts.system import SYSTEM_PROMPT
from <agent_name>.tools.base import get_tools
from <agent_name> import profiles  # noqa: F401 — registers HarnessProfile entries

# ---------------------------------------------------------------------------
# Permissions — deny-by-default, allowlist narrow.
# ---------------------------------------------------------------------------

PERMISSIONS: list[FileSystemPermission] = [
    # Read the workspace freely.
    FileSystemPermission(operation="read",  path_pattern="/workspace/**", mode="allow"),

    # Write only into the drafts subtree.
    FileSystemPermission(operation="write", path_pattern="/workspace/drafts/**", mode="allow"),

    # Defence-in-depth denies (caught by the catch-all below too, but explicit).
    FileSystemPermission(operation="read",  path_pattern="**/.env*",     mode="deny"),
    FileSystemPermission(operation="read",  path_pattern="**/.ssh/**",   mode="deny"),
    FileSystemPermission(operation="read",  path_pattern="**/secrets/**", mode="deny"),

    # Catch-all: deny everything else.
    FileSystemPermission(operation="read",  path_pattern="**", mode="deny"),
    FileSystemPermission(operation="write", path_pattern="**", mode="deny"),
]

# ---------------------------------------------------------------------------
# Side-effecting tools that must pause for human approval in production.
# ---------------------------------------------------------------------------

INTERRUPT_ON_PROD: dict[str, bool] = {
    "send_email":    True,
    "delete_email":  True,
    "post_to_slack": True,
}


def build_agent(dev_mode: bool = False):
    """Build the compiled deep-agent graph.

    Args:
        dev_mode: when True, approval / interrupt gating is disabled and
            iteration is fast. Production runs MUST pass ``False``.

    Returns:
        The compiled deep-agent graph, ready for ``ainvoke`` / ``astream``.
    """
    tools, _ = get_tools(dev_mode=dev_mode)
    interrupt_on = {} if dev_mode else INTERRUPT_ON_PROD

    return create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        permissions=PERMISSIONS,
        interrupt_on=interrupt_on,
        memory=["./AGENTS.md"],
        # subagents=...  # omit to use the default general-purpose subagent
    )


graph = build_agent(dev_mode=False)
"""Compiled deep-agent graph exported for ``langgraph.json``."""
