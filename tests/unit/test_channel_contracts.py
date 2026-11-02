"""Pure contracts of the WhatsApp adapter and the Drive export envelopes (no database, no network)."""

import hashlib
import hmac
from uuid import uuid4

import pytest
from luma.core.config import settings
from luma.features.google_sync.exports import ReceiptRequest, drive_filename
from luma.features.messaging.allowlist import allowed_senders
from luma.features.messaging.webhook import message_event, status_event, valid_signature
from luma.features.messaging.whatsapp_client import GraphError, media_host_allowed
from pydantic import ValidationError


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        ("https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1", True),
        ("https://graph.facebook.com/v26.0/123", True),
        ("https://scontent.xx.fbcdn.net/x", True),
        ("http://lookaside.fbsbx.com/x", False),
        ("https://fbsbx.com.attacker.example/x", False),
        ("https://attacker.example/lookaside.fbsbx.com", False),
        ("https://evilfbsbx.com/x", False),
        ("//lookaside.fbsbx.com/x", False),
        ("", False),
    ],
)
def test_media_hosts_must_be_meta_owned_https(url, allowed):
    """The bearer token is attached only to HTTPS URLs on Meta-owned hosts, never lookalikes."""
    assert media_host_allowed(url) is allowed


def test_graph_error_codes_are_short_and_opaque():
    """Provider text can never leak through an error code: it is lower-cased, stripped and capped."""
    error = GraphError("rejected", "131047 <script>Re-engagement\nmessage with token abc!" + "x" * 80)
    assert error.kind == "rejected" and len(error.code) <= 40
    assert all(c.isalnum() or c == "_" for c in error.code)
    assert GraphError("unknown", "!!!").code == "error"


def test_signature_requires_the_sha256_prefix_hex_and_the_exact_body(monkeypatch):
    """Only `sha256=<64 hex>` over the raw bytes verifies; case, prefix and body changes all fail."""
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "secret-value")
    settings.cache_clear()
    body = b'{"a":"caf\\u00e9"}'
    good = hmac.new(b"secret-value", body, hashlib.sha256).hexdigest()
    assert valid_signature(body, f"sha256={good}")
    assert not valid_signature(body + b" ", f"sha256={good}")
    assert not valid_signature(body, f"sha1={good}")
    assert not valid_signature(body, good)
    assert not valid_signature(body, f"sha256={good.upper()}")
    assert not valid_signature(body, "sha256=" + good[:-1])
    settings.cache_clear()


def test_inbound_events_are_reduced_to_minimum_validated_fields():
    """Malformed identities and media ids are dropped; accepted events keep only what the worker needs."""
    text = message_event(
        {"id": "wamid.1", "from": "15551234567", "type": "text", "text": {"body": "x" * 5000, "extra": 1}},
        {"15551234567": "Ann"},
    )
    assert text == {"id": "wamid.1", "from": "15551234567", "type": "text", "name": "Ann", "text": "x" * 4000}
    assert message_event({"id": "wamid.2", "from": "not-a-number", "type": "text"}, {}) is None
    assert message_event({"id": "", "from": "15551234567", "type": "text"}, {}) is None
    assert (
        message_event({"id": "w", "from": "15551234567", "type": "audio", "audio": {"id": "12/../3"}}, {})
        is None
    )
    audio = message_event(
        {
            "id": "w",
            "from": "15551234567",
            "type": "audio",
            "audio": {"id": "123", "mime_type": "audio/ogg; codecs=opus"},
        },
        {},
    )
    assert audio["media_id"] == "123"
    assert status_event({"id": "w", "status": "delivered"}) == {"id": "w", "status": "delivered", "code": ""}
    assert status_event({"id": "w", "status": "weird"}) is None
    failed = status_event({"id": "w", "status": "failed", "errors": [{"code": 131047, "title": "free text"}]})
    assert failed["code"] == "131047"


def test_allowlist_parses_plus_whitespace_and_empty(monkeypatch):
    """An empty setting admits nobody; numbers are compared as digits."""
    for value, expected in (("", set()), (" +1555, 1556 ,", {"1555", "1556"})):
        monkeypatch.setenv("WHATSAPP_TEST_RECIPIENTS", value)
        settings.cache_clear()
        assert allowed_senders() == expected
    settings.cache_clear()


def base_receipt(**overrides):
    """Build a valid signed-envelope body for the receipt model."""
    return {
        "schema_version": 1,
        "company_id": str(uuid4()),
        "spreadsheet_id": "sheet",
        "timestamp": 1,
        "nonce": str(uuid4()),
        "event": "drive_export_receipt",
        "export_id": str(uuid4()),
        "claim_token": str(uuid4()),
        **overrides,
    }


@pytest.mark.parametrize(
    "fields",
    [
        {"outcome": "stored"},
        {"outcome": "stored", "drive_file_id": "abc", "sha256": "0" * 64},
        {"outcome": "stored", "drive_file_id": "a/b", "sha256": "0" * 64, "size": 5},
        {"outcome": "stored", "drive_file_id": "abc", "sha256": "G" * 64, "size": 5},
        {"outcome": "stored", "drive_file_id": "abc", "sha256": "0" * 64, "size": 0},
        {"outcome": "failed"},
        {"outcome": "failed", "error_code": "Drive Error!"},
        {"outcome": "stored", "drive_file_id": "abc", "sha256": "0" * 64, "size": 5, "extra": 1},
    ],
)
def test_receipt_models_reject_incomplete_or_unsafe_outcomes(fields):
    """A stored receipt needs a Drive id, digest and size; a failure needs a safe code; unknown fields are refused."""
    with pytest.raises(ValidationError):
        ReceiptRequest.model_validate(base_receipt(**fields))


def test_valid_receipts_and_drive_filenames():
    """Both outcome shapes validate, and Drive file names never contain path or control characters."""
    ReceiptRequest.model_validate(
        base_receipt(outcome="stored", drive_file_id="1AbC_-9", sha256="a" * 64, size=10)
    )
    ReceiptRequest.model_validate(base_receipt(outcome="failed", error_code="drive_error"))
    name = drive_filename({"number": "Q/../2026\n-0001", "revision": 3})
    assert name.endswith("-r3.pdf") and "/" not in name and "\n" not in name
