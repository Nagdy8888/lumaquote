"""Exact accept and decline phrase table (D49): what binds a customer and what stays ordinary text."""

import pytest
from luma.features.messaging.email_ingress import strip_quoted
from luma.features.orders.acceptance import parse_answer


@pytest.mark.parametrize(
    "text",
    [
        "accept",
        "Accept",
        "ACCEPT!",
        "ACCEPT.",
        "  i accept the quotation. ",
        "I   Accept",
        "accepted",
        "yes i accept",
        "Yes, I accept!",
        "accept quotation",
        "Accept The Quotation",
        "accept!!",
    ],
)
def test_accept_phrases(text):
    """Every table phrase accepts, whatever its case, spacing or trailing punctuation."""
    assert parse_answer(text) == "accept"


@pytest.mark.parametrize(
    "text",
    ["decline", "DECLINE!", " I decline. ", "declined", "reject", "No thanks", "decline quotation", "Decline  Quotation."],
)
def test_decline_phrases(text):
    """Every decline phrase declines."""
    assert parse_answer(text) == "decline"


@pytest.mark.parametrize(
    "text",
    [
        "yes",
        "Yes!",
        "ok",
        "no",
        "",
        "   ",
        ".",
        "accept but change qty to 20",
        "please accept",
        "accept? what is the price",
        "i do not accept",
        "dont accept",
        "accept\nthanks",
        "accept, thanks",
        "no thanks, send a cheaper one",
        "decline and re-quote",
        "yes please quote 3 DL-001",
        "accept " * 20,
        "x" * 500,
        "acceptt",
    ],
)
def test_everything_else_is_ordinary_text(text):
    """Plain yes (D46), qualified answers, questions and long text are never an acceptance."""
    assert parse_answer(text) is None


def test_non_text_is_not_an_answer():
    """Defensive: a non-string input is never an answer."""
    assert parse_answer(None) is None  # type: ignore[arg-type]


def test_an_email_reply_with_quoted_history_reduces_to_the_phrase():
    """strip_quoted leaves only the new text, so a Gmail reply 'Accept' above the history still parses."""
    body = "Accept\n\nOn Sat, Nov 7, 2026 at 5:00 PM Luma <me@example.org> wrote:\n> Quotation LQ-1, revision 1.\n> Reply ACCEPT to accept or DECLINE to decline."
    assert parse_answer(strip_quoted(body)) == "accept"
    assert parse_answer(strip_quoted("> Reply ACCEPT to accept\nAccept")) is None
