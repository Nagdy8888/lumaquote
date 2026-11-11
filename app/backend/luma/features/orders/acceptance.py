"""Recognize a customer's accept or decline answer with fixed phrases, never with AI (decision D49).

The decision to bind a customer to a quotation is a commercial act, so it is made by a small
exact phrase table. One bare courtesy ("thanks", "thank you", "thx", "many thanks") before or
after a phrase is ignored because it adds no terms. Anything else that is not exactly one of
these phrases is ordinary customer text and keeps today's behavior (supersede the offer and
re-quote). In particular a plain "yes" is not an acceptance: decision D46 uses YES to confirm an
order restatement before a paid AI call.
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
COURTESY = r"(?:many thanks|thanks a lot|thank you|thanks|thx)"
LEADING_COURTESY = re.compile(rf"^{COURTESY}[,.!]?\s+")
TRAILING_COURTESY = re.compile(rf"[,.!]?\s+{COURTESY}$")
MAX_MESSAGE_LENGTH = 60


def parse_answer(text: str) -> str | None:
    """Return 'accept', 'decline' or None for one customer message.

    Input is untrusted customer text. It is lowercased, trimmed, its runs of whitespace (line
    breaks included) are collapsed and trailing `.` and `!` characters are removed; one leading
    and one trailing courtesy word ("thanks", "thank you", ...) are dropped. The whole message must
    be at most 60 characters and the rest must equal one phrase of the table (at most 40), so
    "accept, thanks" accepts while "accept but change qty to 20" and "please accept" are
    ordinary text. Pure function: no I/O and no side effects. Callers still have to prove that
    a valid quotation exists before acting (`service.answer_quote`).
    """
    if not isinstance(text, str) or len(text) > 200:
        return None
    normalized = SPACES.sub(" ", text.strip().lower()).rstrip(".!").strip()
    if not normalized or len(normalized) > MAX_MESSAGE_LENGTH:
        return None
    # The table is matched before courtesy is dropped, so "no thanks" stays a whole phrase.
    exact = _lookup(normalized)
    if exact:
        return exact
    normalized = LEADING_COURTESY.sub("", normalized, count=1)
    normalized = TRAILING_COURTESY.sub("", normalized, count=1).rstrip(".!,").strip()
    if not normalized or len(normalized) > MAX_ANSWER_LENGTH:
        return None
    return _lookup(normalized)


def _lookup(normalized: str) -> str | None:
    """Map an already-normalized message to 'accept', 'decline' or None by exact table membership."""
    if normalized in ACCEPT_PHRASES:
        return "accept"
    if normalized in DECLINE_PHRASES:
        return "decline"
    return None
