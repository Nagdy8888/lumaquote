"""Send-email tool for the <agent_name> agent.

Wraps the Gmail service's ``send`` method as an LLM-callable ``@tool``.
The wrap is intentionally thin: validation, send, return id. Approval
gating is applied externally in ``tools/base.py::get_tools``.
"""
from __future__ import annotations

from langchain_core.tools import tool

from services.gmail.client import GmailClient
from <agent_name>.settings import settings


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to the given recipient.

    Use this tool to deliver a drafted reply or notification. The tool
    blocks until the Gmail API confirms the send and returns the message
    id, which the agent should record in its plan.

    Args:
        to: recipient email address. Must be a valid RFC-5322 address.
        subject: subject line. Keep under 200 characters.
        body: plain-text body. Markdown is rendered as plain text.

    Returns:
        The sent message id (provider-specific opaque string).

    Raises:
        GmailError: when the API rejects the request (auth, quota, bad
            payload). The agent should surface this to the user and ask
            whether to retry or abort.
    """
    return GmailClient(settings.gmail).send(to=to, subject=subject, body=body)
