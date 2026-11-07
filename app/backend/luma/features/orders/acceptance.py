"""Recognize a customer's accept or decline answer with fixed phrases, never with AI (decision D49).

The decision to bind a customer to a quotation is a commercial act, so it is made by a small
exact phrase table. Anything that is not exactly one of these phrases is ordinary customer text and
keeps today's behavior (supersede the offer and re-quote). In particular a plain "yes" is not an
acceptance: decision D46 uses YES to confirm an order restatement before a paid AI call.
"""

import re

MAX_ANSWER_LENGTH = 40
ACCEPT_PHRASES = frozenset(
    {
        "accept",
        "i accept",
        "accepted",
        "yes i accept",
        "yes, i accept",
        "accept quotation",
        "accept the quotation",
        "i accept the quotation",
    }
)
DECLINE_PHRASES = frozenset({"decline", "i decline", "declined", "reject", "no thanks", "decline quotation"})
SPACES = re.compile(r"\s+")


def parse_answer(text: str) -> str | None:
    """Return 'accept', 'decline' or None for one customer message.

    Input is untrusted customer text. It is lowercased, trimmed, its runs of whitespace are
    collapsed and trailing `.` and `!` characters are removed. The whole message must then equal
    one phrase of the table and be at most 40 characters, so "accept but change qty to 20" is
    ordinary text. Pure function: no I/O and no side effects. Callers still have to prove that
    a valid quotation exists before acting (`service.answer_quote`).
    """
    if not isinstance(text, str) or len(text) > 200:
        return None
    normalized = SPACES.sub(" ", text.strip().lower()).rstrip(".!").strip()
    if not normalized or len(normalized) > MAX_ANSWER_LENGTH:
        return None
    if normalized in ACCEPT_PHRASES:
        return "accept"
    if normalized in DECLINE_PHRASES:
        return "decline"
    return None
