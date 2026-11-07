"""Twilio signature and signed-media-link rules, checked against Twilio's own published test vector.

`local` evidence only: proves the algorithm matches twilio-python's `RequestValidator` vector
and that media links expire and bind to one outbox id. It does not prove Twilio reaches the
gateway; that is a live step in docs/MORNING_ACTIONS.md.
"""

from uuid import uuid4

import pytest
from luma.core.config import settings
from luma.core.errors import DomainError
from luma.features.messaging import media_links
from luma.features.messaging.twilio_webhook import expected_signature, url_variants


@pytest.fixture
def token(monkeypatch):
    """Configure the Twilio Auth Token used by Twilio's own validator unit test."""
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "12345")
    monkeypatch.setenv("PUBLIC_GATEWAY_URL", "https://gateway.example")
    settings.cache_clear()
    yield
    settings.cache_clear()


def test_signature_matches_twilio_python_vector(token):
    """twilio-python tests/unit/test_request_validator.py: token 12345 -> RSOYDt4T1cUTdK1PDd93/VVr8B8=."""
    params = {
        "CallSid": ["CA1234567890ABCDE"],
        "Digits": ["1234"],
        "From": ["+14158675309"],
        "To": ["+18005551212"],
        "Caller": ["+14158675309"],
    }
    assert expected_signature("https://mycompany.com/myapp.php?foo=1&bar=2", params) == "RSOYDt4T1cUTdK1PDd93/VVr8B8="
    params["Digits"] = ["1235"]
    assert expected_signature("https://mycompany.com/myapp.php?foo=1&bar=2", params) != "RSOYDt4T1cUTdK1PDd93/VVr8B8="


def test_url_variants_add_or_remove_the_default_port():
    """Twilio may sign with or without an explicit port; both forms are tried, nothing else."""
    assert url_variants("https://a.example/webhooks/twilio") == (
        "https://a.example/webhooks/twilio",
        "https://a.example:443/webhooks/twilio",
    )
    assert url_variants("https://a.example:443/x") == ("https://a.example:443/x", "https://a.example/x")


def test_media_link_binds_outbox_id_and_expires(token):
    """A link verifies only for its own outbox id and expiry; the signature changes with either."""
    outbox = str(uuid4())
    url = media_links.quotation_url(outbox, now=1_000)
    _, _, tail = url.partition("/media/quotations/")
    identity, expires, supplied, name = tail.split("/")
    assert (identity, int(expires), name) == (outbox, 1_000 + media_links.TTL_SECONDS, "quotation.pdf")
    assert supplied == media_links.signature(outbox, int(expires))
    assert supplied != media_links.signature(str(uuid4()), int(expires))
    assert supplied != media_links.signature(outbox, int(expires) + 1)
    assert url.startswith("https://gateway.example/")


def test_media_link_refuses_without_a_token(monkeypatch):
    """No Auth Token means no key, so links can be neither minted nor verified."""
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "")
    settings.cache_clear()
    with pytest.raises(DomainError):
        media_links.quotation_url(str(uuid4()))
    settings.cache_clear()
