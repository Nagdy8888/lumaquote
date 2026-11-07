"""Twilio WhatsApp Sandbox channel (D43) against real PostgreSQL with a mock Twilio transport.

`local-substitute` evidence: the gateway, worker and sender run for real, but Twilio is an
in-process `httpx.MockTransport` and webhooks are signed here with the documented algorithm.
These tests prove the ingress/egress contract (signature, tenant mapping, deduplication,
allowlist, media auth and redirect rules, uncertain outcomes, monotonic receipts, exact PDF
bytes behind the signed link). They do NOT prove Twilio accepts these requests, that a tunnel
reaches the gateway or that a phone receives anything; those steps are in docs/MORNING_ACTIONS.md.
"""

import base64
import hashlib
import hmac
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import uuid4

import httpx
import psycopg
import pytest
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.features.messaging import twilio_client
from luma.google_gateway import app
from luma_agent.runtime.delivery import deliver_one
from test_manual_workflow import make_draft, post
from test_voice_intake import wav_bytes
from test_whatsapp import conversation_for, drain, outbox, queue_reply, rows

TOKEN = "twilio-auth-token-for-tests-" + "q" * 8
ACCOUNT = "AC" + "a" * 32
SANDBOX = "14155238886"
SENDER = "15551234567"
PUBLIC = "https://tunnel.example"


def sid(prefix="SM"):
    """Return a fresh, well-formed 34-character Twilio SID."""
    return prefix + uuid4().hex


class Twilio:
    """Recording mock of the Twilio REST API and its media CDN."""

    def __init__(self):
        """Start with healthy defaults: messages accepted, media redirected to a CDN."""
        self.requests = []
        self.send_error = None
        self.media_bytes = b""
        self.redirect = "https://media.cdn.example/blob"

    def handler(self, request: httpx.Request) -> httpx.Response:
        """Answer one request and remember it (including auth header and form body)."""
        self.requests.append(request)
        path = request.url.path
        if request.method == "POST" and path == f"/2010-04-01/Accounts/{ACCOUNT}/Messages.json":
            if self.send_error:
                if isinstance(self.send_error, Exception):
                    raise self.send_error
                return self.send_error
            return httpx.Response(201, json={"sid": sid(), "status": "queued"})
        if request.method == "GET" and request.url.host == "api.twilio.com" and "/Media/" in path:
            return httpx.Response(307, headers={"location": self.redirect})
        if request.method == "GET":
            return httpx.Response(200, content=self.media_bytes)
        return httpx.Response(404)

    def sent(self):
        """Return message-create requests with their parsed form fields."""
        return [
            (r, {k: v[0] for k, v in parse_qs(r.content.decode()).items()})
            for r in self.requests
            if r.method == "POST" and r.url.path.endswith("/Messages.json")
        ]


@pytest.fixture
def twilio(environment, monkeypatch):
    """Configure Twilio as the active provider for the isolated company; route REST calls to the mock."""
    fake = Twilio()
    values = {
        "WHATSAPP_PROVIDER": "twilio",
        "TWILIO_ACCOUNT_SID": ACCOUNT,
        "TWILIO_AUTH_TOKEN": TOKEN,
        "TWILIO_WHATSAPP_FROM": SANDBOX,
        "PUBLIC_GATEWAY_URL": PUBLIC,
        "WHATSAPP_COMPANY_ID": str(environment["company"]),
        "WHATSAPP_TEST_RECIPIENTS": f"+{SENDER}",
        "WHATSAPP_TOKEN": "",
        "ENABLE_LIVE_WHATSAPP": "true",
        "ENABLE_PAID_AI": "false",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    settings.cache_clear()
    monkeypatch.setattr(
        twilio_client, "make_client", lambda: httpx.Client(transport=httpx.MockTransport(fake.handler))
    )
    return fake


def sign(url: str, fields: dict, token: str = TOKEN) -> str:
    """Sign like Twilio: URL + sorted name+value pairs, HMAC-SHA1, base64."""
    data = url + "".join(name + fields[name] for name in sorted(fields))
    return base64.b64encode(hmac.new(token.encode(), data.encode(), hashlib.sha1).digest()).decode()


def post_form(path: str, fields: dict, *, token=TOKEN, signature=None, url=None):
    """POST a form body to the real gateway with a signature over the public URL."""
    header = signature if signature is not None else sign(url or PUBLIC + path, fields, token)
    with TestClient(app) as client:
        return client.post(
            path,
            content=urlencode(fields).encode(),
            headers={"X-Twilio-Signature": header, "Content-Type": "application/x-www-form-urlencoded"},
        )


def inbound(body="Please quote 3 DL-001.", message=None, sender=SENDER, **extra):
    """Build an inbound WhatsApp message form as Twilio posts it."""
    return {
        "MessageSid": message or sid(),
        "AccountSid": ACCOUNT,
        "From": f"whatsapp:+{sender}",
        "To": f"whatsapp:+{SANDBOX}",
        "Body": body,
        "NumMedia": "0",
        "ProfileName": "Synthetic Customer",
        "WaId": sender,
        **extra,
    }


def receipt(message, status, code=""):
    """Build a status callback form for one outbound message."""
    fields = {"MessageSid": message, "MessageStatus": status, "AccountSid": ACCOUNT, "From": f"whatsapp:+{SANDBOX}"}
    if code:
        fields["ErrorCode"] = code
    return fields


def count_inbox(env):
    """Return how many inbox rows this tenant has."""
    return rows(env, "select count(*) n from luma.inbox where company_id=%s", env["company"])[0]["n"]


def start(env):
    """Receive one allowlisted text and return its conversation id, with its opening work blocked."""
    assert post_form("/webhooks/twilio", inbound()).status_code == 200
    drain()
    cid = str(conversation_for(env)["id"])
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute("update luma.outbox set status='blocked' where conversation_id=%s", (cid,))
    return cid


def test_signature_tenant_and_configuration_gate_ingress(environment, twilio, monkeypatch):
    """Only correctly signed forms for our account and sandbox number are stored; missing config refuses all."""
    fields = inbound()
    ok = post_form("/webhooks/twilio", fields)
    assert ok.status_code == 200 and ok.headers["content-type"].startswith("text/xml") and "<Response>" in ok.text
    assert post_form("/webhooks/twilio", fields).status_code == 200  # redelivery stored once
    assert post_form("/webhooks/twilio", inbound(), token="wrong-token").status_code == 401
    assert post_form("/webhooks/twilio", inbound(), signature="").status_code == 401
    tampered = inbound()
    good = sign(PUBLIC + "/webhooks/twilio", tampered)
    tampered["Body"] = "changed after signing"
    assert post_form("/webhooks/twilio", tampered, signature=good).status_code == 401
    port = inbound()
    assert post_form("/webhooks/twilio", port, url="https://tunnel.example:443/webhooks/twilio").status_code == 200
    assert post_form("/webhooks/twilio", inbound(AccountSid="AC" + "b" * 32)).status_code == 200
    assert post_form("/webhooks/twilio", inbound(To="whatsapp:+15550009999")).status_code == 200
    with TestClient(app) as client:
        assert client.post("/webhooks/twilio", content=b"x" * 1_048_577).status_code == 413
    assert count_inbox(environment) == 2  # first message + port variant; foreign account/number dropped
    monkeypatch.setenv("WHATSAPP_PROVIDER", "meta")
    settings.cache_clear()
    assert post_form("/webhooks/twilio", inbound()).status_code == 503


def test_text_creates_a_conversation_for_allowlisted_senders_only(environment, twilio):
    """An allowlisted sender opens a WhatsApp conversation; anyone else is ignored."""
    post_form("/webhooks/twilio", inbound(sender="15559990000"))
    drain()
    assert rows(environment, "select 1 from luma.conversations where company_id=%s", environment["company"]) == []
    cid = start(environment)
    [message] = rows(environment, "select * from luma.messages where conversation_id=%s and actor='customer'", cid)
    assert message["provider_id"].startswith("SM")


def test_voice_note_uses_auth_on_twilio_only_and_enters_the_media_pipeline(environment, twilio):
    """Media is fetched by SID with Basic auth; the CDN redirect is followed without credentials."""
    twilio.media_bytes = wav_bytes()
    message, media = sid("MM"), sid("ME")
    fields = inbound(
        body="",
        message=message,
        NumMedia="1",
        MediaContentType0="audio/wav",
        MediaUrl0=f"https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT}/Messages/{message}/Media/{media}",
    )
    assert post_form("/webhooks/twilio", fields).status_code == 200
    drain()
    cid = conversation_for(environment)["id"]
    [stored] = rows(environment, "select * from luma.media where conversation_id=%s", cid)
    environment["files"].append(stored["original_path"])
    assert stored["kind"] == "audio"
    api, cdn = twilio.requests
    assert api.url.host == "api.twilio.com" and api.headers["authorization"].startswith("Basic ")
    assert cdn.url.host == "media.cdn.example" and "authorization" not in cdn.headers


@pytest.mark.parametrize(
    ("mime", "redirect", "media_account"),
    [
        ("application/zip", "https://media.cdn.example/blob", ACCOUNT),
        ("audio/wav", "http://media.cdn.example/blob", ACCOUNT),
        ("audio/wav", "https://media.cdn.example/blob", "AC" + "c" * 32),
    ],
    ids=["mime-denied", "plain-http-redirect", "foreign-account-url"],
)
def test_hostile_media_is_refused_without_storing(environment, twilio, mime, redirect, media_account):
    """A denied type, a non-HTTPS redirect or a media URL for another account stores nothing."""
    twilio.media_bytes = wav_bytes()
    twilio.redirect = redirect
    message, media = sid("MM"), sid("ME")
    fields = inbound(
        body="",
        message=message,
        NumMedia="1",
        MediaContentType0=mime,
        MediaUrl0=f"https://api.twilio.com/2010-04-01/Accounts/{media_account}/Messages/{message}/Media/{media}",
    )
    post_form("/webhooks/twilio", fields)
    drain()
    assert rows(environment, "select 1 from luma.media where company_id=%s", environment["company"]) == []
    if mime == "application/zip":
        assert twilio.requests == []  # refused before any network call


def test_text_reply_is_submitted_once_as_a_twilio_message(environment, twilio):
    """An authorized reply posts one form to Messages.json and is recorded as submitted with its SID."""
    cid = start(environment)
    queue_reply(environment, cid)
    assert deliver_one(environment["company"]) is True
    assert deliver_one(environment["company"]) is False
    [(request, form)] = twilio.sent()
    assert form == {
        "From": f"whatsapp:+{SANDBOX}",
        "To": f"whatsapp:+{SENDER}",
        "Body": "Which colour temperature?",
        "StatusCallback": f"{PUBLIC}/webhooks/twilio/status",
    }
    assert request.headers["authorization"] == "Basic " + base64.b64encode(f"{ACCOUNT}:{TOKEN}".encode()).decode()
    [row] = [r for r in outbox(environment, cid) if r["status"] != "blocked"]
    assert row["status"] == "submitted" and row["provider_id"].startswith("SM")


@pytest.mark.parametrize(
    ("failure", "status", "code"),
    [
        (httpx.ReadTimeout("slow"), "unknown", "transport_error"),
        (httpx.Response(503, json={}), "unknown", "http_503"),
        (httpx.Response(400, json={"code": 63015, "message": "not joined"}), "failed", "twilio_63015"),
        (httpx.ConnectError("down"), "failed", "connect_error"),
        (httpx.Response(201, json={"status": "queued"}), "unknown", "no_message_id"),
    ],
    ids=["timeout", "server-error", "rejected", "unreachable", "no-sid"],
)
def test_uncertain_and_failed_submissions_are_never_retried(environment, twilio, failure, status, code):
    """Timeouts, 5xx and a 2xx without a SID are `unknown`; definite refusals are `failed`; one attempt only."""
    cid = start(environment)
    queue_reply(environment, cid)
    twilio.send_error = failure
    assert deliver_one(environment["company"]) is True
    assert deliver_one(environment["company"]) is False
    assert len(twilio.sent()) == 1
    [row] = [r for r in outbox(environment, cid) if r["status"] != "blocked"]
    assert (row["status"], row["error_code"], row["provider_id"]) == (status, code, None)


def test_receipts_advance_monotonically_and_undelivered_fails(environment, twilio):
    """sent/delivered/read only advance; queued is ignored; undelivered fails an unconfirmed send."""
    cid = start(environment)
    queue_reply(environment, cid)
    deliver_one(environment["company"])
    [row] = [r for r in outbox(environment, cid) if r["status"] == "submitted"]
    message = row["provider_id"]

    def apply(state, code=""):
        """Deliver one signed status callback and process it."""
        assert post_form("/webhooks/twilio/status", receipt(message, state, code)).status_code == 200
        drain()
        return [r for r in outbox(environment, cid) if r["provider_id"] == message][0]["status"]

    assert apply("queued") == "submitted"
    assert apply("read") == "read"
    assert apply("delivered") == "read"
    assert apply("undelivered", "63016") == "read"
    queue_reply(environment, cid, "Second question?")
    deliver_one(environment["company"])
    [second] = [r for r in outbox(environment, cid) if r["status"] == "submitted"]
    post_form("/webhooks/twilio/status", receipt(second["provider_id"], "undelivered", "63016"))
    drain()
    [failed] = [r for r in outbox(environment, cid) if r["provider_id"] == second["provider_id"]]
    assert (failed["status"], failed["error_code"]) == ("failed", "twilio_63016")


def test_approved_quotation_is_offered_as_the_exact_pdf_behind_a_signed_link(environment, twilio):
    """The send carries a signed media link; it serves the staff PDF bytes and refuses tampering."""
    cid = start(environment)
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute(
            "update luma.snapshots set source='google_sheets',observed_at=now() where company_id=%s",
            (environment["company"],),
        )
    quote = make_draft(environment, cid)
    environment["files"].append(f"{environment['company']}/quotes/{quote['id']}.pdf")
    decision = post(environment, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"})
    assert decision.status_code == 200
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute("update luma.snapshots set observed_at=now() where company_id=%s", (environment["company"],))
    deliver_one(environment["company"])
    [(_, form)] = twilio.sent()
    assert "Total USD" in form["Body"] and form["MediaUrl"].startswith(f"{PUBLIC}/media/quotations/")
    path = urlsplit(form["MediaUrl"]).path
    staff_pdf = environment["api"].get(f"/api/quotes/{quote['id']}/pdf", headers=environment["headers"]).content
    with TestClient(app) as client:
        served = client.get(path)
        assert served.status_code == 200 and served.content == staff_pdf
        assert served.headers["content-type"] == "application/pdf"
        parts = path.split("/")
        forged = "/".join([*parts[:5], "0" * 64, parts[6]])
        assert client.get(forged).status_code == 404
        other = "/".join([*parts[:3], str(uuid4()), *parts[4:]])
        assert client.get(other).status_code == 404
    [row] = [r for r in outbox(environment, cid) if r["kind"] == "quotation"]
    assert row["status"] == "submitted"
