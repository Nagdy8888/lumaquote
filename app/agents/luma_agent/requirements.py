"""Deterministic safety policy between untrusted extraction and consequential preparation."""

import re

from .schemas import Extraction

QUESTION = "Please confirm each product SKU and quantity, for example: 3 DL-001."
MEDIA_QUESTION = "Please confirm each product SKU and quantity in a text reply, for example: 3 DL-001."


def clarification_for(result: Extraction, messages: list[dict], *, media: bool) -> str | None:
    """Choose a fixed safe question; media requires explicit matching written values, never a generic acknowledgment.

    Messages are newest first. Model-generated prose is never outbound authority.
    Duplicate SKUs are ambiguous rather than silently summed or overwritten.
    This gate establishes explicit fields only; catalog and price checks remain downstream.
    """
    lines = result.lines
    if result.uncertain_critical_fields or not lines:
        return MEDIA_QUESTION if media else QUESTION
    requested = []
    for line in lines:
        if not line.sku or not line.quantity or not re.fullmatch(r"[A-Z]{2}-\d{3}", line.sku):
            return QUESTION
        requested.append((line.sku, line.quantity))
    if len({sku for sku, _ in requested}) != len(requested):
        return QUESTION
    if media:
        if not messages or messages[0]["kind"] != "text":
            return MEDIA_QUESTION
        confirmed = [
            (sku, int(qty))
            for qty, sku in re.findall(r"\b(\d{1,5})\s+([A-Z]{2}-\d{3})\b", messages[0]["body"].upper())
        ]
        if sorted(confirmed) != sorted(requested):
            return MEDIA_QUESTION
    return None
