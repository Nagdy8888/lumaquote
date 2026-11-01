"""Deterministic safety policy between untrusted extraction and consequential preparation."""

import re

from .schemas import Extraction
from .written_requests import parse_written_request

QUESTION = "Please confirm each product SKU and quantity, for example: 3 DL-001."
MEDIA_QUESTION = "Please confirm each product SKU and quantity in a text reply, for example: 3 DL-001."


def clarification_for(result: Extraction, messages: list[dict], *, media: bool) -> str | None:
    """Require a complete positive written order matching all untrusted extracted fields.

    Messages are newest first; only the latest customer text can confirm fields,
    including text-only requests. The deterministic whole-message grammar rejects
    negation/alternatives rather than searching for pairs within arbitrary prose.
    Model-generated wording, old turns and readable media cannot supply consent.
    Duplicate, missing, extra or mismatched lines always clarify. This gate grants
    field provenance only; catalog, pricing, availability and staff approval remain
    downstream. No message, draft, provider call or database write occurs here.
    """
    question = MEDIA_QUESTION if media else QUESTION
    lines = result.lines
    if result.uncertain_critical_fields or not lines:
        return question
    requested = []
    for line in lines:
        if not line.sku or not line.quantity or not re.fullmatch(r"[A-Z]{2}-\d{3}", line.sku):
            return question
        requested.append((line.sku, line.quantity))
    if len({sku for sku, _ in requested}) != len(requested):
        return question
    if not messages or messages[0]["kind"] != "text":
        return question
    confirmed = parse_written_request(messages[0]["body"])
    if confirmed is None or sorted(confirmed) != sorted(requested):
        return question
    return None
