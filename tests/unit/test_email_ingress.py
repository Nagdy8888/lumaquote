"""Pure Gmail ingress rules (D47): sender address, Gmail authentication, quoted-reply stripping, reduction."""

import pytest
from luma.features.messaging.email_ingress import (
    MailItem,
    reduce_mail,
    sender_address,
    sender_authenticated,
    strip_quoted,
)

GOOD = (
    "mx.google.com; dkim=pass header.i=@example.com header.s=s1 header.b=abc; "
    "spf=pass (google.com: domain of customer@example.com designates 192.0.2.1 as permitted sender) "
    "smtp.mailfrom=customer@example.com; dmarc=pass (p=NONE sp=NONE dis=NONE) header.from=example.com"
)


@pytest.mark.parametrize("header,expected", [
    ("Customer <Customer@Example.com>", "customer@example.com"),
    ("customer@example.com", "customer@example.com"),
    ('"Name, Inc" <a.b+c@sub.example.co>', "a.b+c@sub.example.co"),
    ("Not an address", ""),
    ("", ""),
])
def test_sender_address(header, expected):
    """Only one well-formed address is returned, lowercase."""
    assert sender_address(header) == expected


def test_gmail_pass_authenticates_the_from_domain():
    """A Gmail-added header with passing checks for the From domain authenticates it."""
    assert sender_authenticated(GOOD, "customer@example.com")


@pytest.mark.parametrize("results", [
    "mx.google.com; dmarc=pass header.from=example.com",
    "mx.google.com; dkim=pass header.i=@example.com header.s=x",
    "mx.google.com; dkim=pass header.d=example.com",
    "mx.google.com; spf=pass smtp.mailfrom=bounce@example.com",
])
def test_each_passing_mechanism_counts(results):
    """DMARC, DKIM or SPF passing for the From domain is enough."""
    assert sender_authenticated(results, "customer@example.com")


@pytest.mark.parametrize("results,address", [
    ("", "customer@example.com"),
    ("attacker.example; dmarc=pass header.from=example.com", "customer@example.com"),
    ("mx.google.com; dmarc=fail header.from=example.com", "customer@example.com"),
    ("mx.google.com; dmarc=pass header.from=evil.example", "customer@example.com"),
    ("mx.google.com; dkim=pass header.i=@example.com.evil.example", "customer@example.com"),
    ("mx.google.com; spf=pass smtp.mailfrom=x@evil.example", "customer@example.com"),
    ("mx.google.com; spf=softfail smtp.mailfrom=x@example.com", "customer@example.com"),
    (GOOD, "not-an-address"),
])
def test_anything_else_is_unauthenticated(results, address):
    """Wrong authserv-id, failing checks or another domain never authenticate."""
    assert not sender_authenticated(results, address)


@pytest.mark.parametrize("body,expected", [
    ("yes\n\nOn Sat, Nov 7, 2026 at 5:00 PM Luma <me@example.com> wrote:\n> To confirm ...", "yes"),
    ("yes\n\nOn Sat, Nov 7, 2026 at 5:00 PM Luma <me@example.com>\nwrote:\n> old", "yes"),
    ("I need 5 DL-001\n> quoted", "I need 5 DL-001"),
    ("I need 5 DL-001\n-- \nMy signature", "I need 5 DL-001"),
    ("نعم\n\nفي السبت، 7 نوفمبر 2026 كتب Luma:\n> old", "نعم"),
    ("ok\n-----Original Message-----\nFrom: x", "ok"),
    ("line one\nline two", "line one\nline two"),
])
def test_quoted_history_is_removed(body, expected):
    """Only the new part of a reply reaches the agent."""
    assert strip_quoted(body) == expected


def item(**fields):
    """Build a valid mail with overridable fields."""
    base = {
        "message_id": "18c0ffee12345678",
        "thread_id": "18c0ffee00000001",
        "from_header": "Customer <customer@example.com>",
        "subject": "Quote request",
        "date_ms": 1,
        "auth_results": GOOD,
        "body": "i want 5 dl-001",
    }
    return MailItem.model_validate({**base, **fields})


def test_reduce_builds_an_email_event():
    """The event carries channel, sender, thread, authentication and the stripped text."""
    provider_id, kind, event = reduce_mail(item())
    assert (provider_id, kind) == ("gm:18c0ffee12345678", "message")
    assert event["channel"] == "email" and event["from"] == "customer@example.com"
    assert event["authenticated"] is True and event["type"] == "text" and event["text"] == "i want 5 dl-001"


def test_empty_body_uses_subject_and_attachments_only_is_unsupported():
    """A subject-only request is read from the subject; attachments alone get the fixed notice."""
    assert reduce_mail(item(body=""))[2]["text"] == "Quote request"
    assert reduce_mail(item(body="", subject="", attachments=2))[2]["type"] == "unsupported"


def test_unparseable_sender_is_skipped():
    """A From header without an address is not stored."""
    assert reduce_mail(item(from_header="Undisclosed recipients")) is None
