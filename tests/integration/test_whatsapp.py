"""WhatsApp channel against real PostgreSQL with a mock Graph transport; no Meta call is ever made.

Everything here is a local substitute: the webhook, worker and sender run for real, but the
provider is an in-process `httpx.MockTransport` that records requests. These tests prove the
ingress/egress contract (signatures, tenant mapping, deduplication, allowlist, media limits,
service window, uncertain outcomes, monotonic receipts, exact PDF bytes). They do NOT prove
Meta accepts these payloads, that a tunnel reaches the gateway or that a phone receives
anything; those are the live steps in docs/MORNING_ACTIONS.md.
"""

import hashlib
import hmac
import json
from uuid import uuid4

import httpx
import psycopg
import pytest
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.features.messaging import whatsapp_client
from luma.features.messaging.inbound import process_next
from luma.google_gateway import app
from luma_agent.runtime.delivery import deliver_one
from psycopg.rows import dict_row
from test_manual_workflow import get_detail, make_draft, post
from test_voice_intake import wav_bytes

SECRET = "meta-app-secret-for-tests-" + "z" * 16
PHONE = "15550001111"
SENDER = "15551234567"


class Graph:
    """Recording mock of the Graph API; routes are configured per test through `.responses`."""

    def __init__(self):
        """Start with healthy defaults for sending, uploading and media lookup."""
        self.requests = []
        self.send_error = None
        self.media_meta = {
            "url": "https://lookaside.fbsbx.com/media/1",
            "mime_type": "audio/wav",
            "file_size": 100,
        }
        self.media_bytes = b""
        self.media_status = 200

    def handler(self, request: httpx.Request) -> httpx.Response:
        """Answer one request and remember it (including the bearer header and body bytes)."""
        self.requests.append(request)
        path = request.url.path
        if request.method == "POST" and path.endswith(f"/{PHONE}/messages"):
            if self.send_error:
                if isinstance(self.send_error, Exception):
                    raise self.send_error
                return self.send_error
            return httpx.Response(200, json={"messages": [{"id": f"wamid.{uuid4().hex}"}]})
        if request.method == "POST" and path.endswith(f"/{PHONE}/media"):
            return httpx.Response(200, json={"id": "99887766"})
        if request.method == "GET" and request.url.host == "graph.facebook.com":
            return httpx.Response(200, json=self.media_meta)
        if request.method == "GET":
            return httpx.Response(self.media_status, content=self.media_bytes)
        return httpx.Response(404)

    def sent(self):
        """Return the message-send requests only (not uploads or lookups)."""
        return [r for r in self.requests if r.method == "POST" and r.url.path.endswith("/messages")]


@pytest.fixture
def graph(environment, monkeypatch):
    """Configure the channel for the isolated company and route every Graph call to the mock."""
    fake = Graph()
    values = {
        "WHATSAPP_APP_SECRET": SECRET,
        "WHATSAPP_VERIFY_TOKEN": "verify-token-for-tests",
        "WHATSAPP_PHONE_ID": PHONE,
        "WHATSAPP_COMPANY_ID": str(environment["company"]),
        "WHATSAPP_TEST_RECIPIENTS": f"+{SENDER}",
        "WHATSAPP_TOKEN": "graph-bearer-token-for-tests",
        "ENABLE_LIVE_WHATSAPP": "true",
        "ENABLE_PAID_AI": "false",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    settings.cache_clear()
    monkeypatch.setattr(
        whatsapp_client, "make_client", lambda: httpx.Client(transport=httpx.MockTransport(fake.handler))
    )
    return fake


def envelope(*, messages=(), statuses=(), phone=PHONE):
    """Build a Meta-shaped webhook payload for the configured (or another) phone number id."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "1555", "phone_number_id": phone},
                            "contacts": [{"profile": {"name": "Synthetic Customer"}, "wa_id": SENDER}],
                            "messages": list(messages),
                            "statuses": list(statuses),
                        },
                    }
                ],
            }
        ],
    }


def text(body, wamid=None, sender=SENDER):
    """Build an inbound text message."""
    return {"from": sender, "id": wamid or f"wamid.{uuid4().hex}", "type": "text", "text": {"body": body}}


def deliver_webhook(payload, *, secret=SECRET, ascii_only=True, header=None):
    """POST raw bytes signed like Meta (sha256=<hex> over the exact body) to the real gateway."""
    raw = json.dumps(payload, ensure_ascii=ascii_only).encode()
    signature = (
        header
        if header is not None
        else "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    )
    with TestClient(app) as client:
        return client.post("/webhooks/whatsapp", content=raw, headers={"X-Hub-Signature-256": signature})


def drain():
    """Process every currently runnable inbox row."""
    while process_next():
        pass


def rows(env, sql, *args):
    """Run a read query against this tenant with a privileged connection."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        return conn.execute(sql, args).fetchall()


def conversation_for(env):
    """Return the WhatsApp conversation created for the test sender."""
    [row] = rows(
        env, "select * from luma.conversations where company_id=%s and channel='whatsapp'", env["company"]
    )
    return row


def start(env, graph_):
    """Receive one allowlisted text and return its WhatsApp conversation id."""
    assert deliver_webhook(envelope(messages=[text("Please quote 3 DL-001.")])).status_code == 200
    drain()
    return str(conversation_for(env)["id"])


def test_handshake_requires_the_exact_verify_token_and_full_configuration(environment, monkeypatch):
    """Only subscribe with the configured token echoes the challenge; missing configuration refuses everything."""
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "right")
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SECRET)
    monkeypatch.setenv("WHATSAPP_PHONE_ID", PHONE)
    monkeypatch.setenv("WHATSAPP_COMPANY_ID", str(environment["company"]))
    settings.cache_clear()
    with TestClient(app) as client:
        ok = client.get(
            "/webhooks/whatsapp",
            params={"hub.mode": "subscribe", "hub.verify_token": "right", "hub.challenge": "12345"},
        )
        assert (ok.status_code, ok.text) == (200, "12345")
        for params in (
            {"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "1"},
            {"hub.mode": "unsubscribe", "hub.verify_token": "right", "hub.challenge": "1"},
            {"hub.mode": "subscribe", "hub.verify_token": "right", "hub.challenge": "<script>"},
        ):
            assert client.get("/webhooks/whatsapp", params=params).status_code == 403
        monkeypatch.setenv("WHATSAPP_APP_SECRET", "")
        settings.cache_clear()
        assert (
            client.get(
                "/webhooks/whatsapp",
                params={"hub.mode": "subscribe", "hub.verify_token": "right", "hub.challenge": "1"},
            ).status_code
            == 503
        )


def test_signature_is_over_exact_raw_bytes_and_bounds_are_enforced(environment, graph):
    """Bad, missing, malformed or wrong-secret signatures fail; ASCII-escaped and UTF-8 bodies both verify."""
    payload = envelope(messages=[text("café 3 DL-001")])
    assert deliver_webhook(payload, secret="not-the-secret").status_code == 401
    assert deliver_webhook(payload, header="sha256=" + "0" * 64).status_code == 401
    assert deliver_webhook(payload, header="").status_code == 401
    assert deliver_webhook(payload, header="md5=" + "a" * 64).status_code == 401
    assert deliver_webhook(payload, ascii_only=True).status_code == 200
    assert deliver_webhook(envelope(messages=[text("café again")]), ascii_only=False).status_code == 200
    with TestClient(app) as client:
        assert client.post("/webhooks/whatsapp", content=b"x" * 1_048_577).status_code == 413
    many = envelope(messages=[text("x") for _ in range(101)])
    assert deliver_webhook(many).status_code == 413
    assert deliver_webhook(envelope(messages=[text("hi")], phone="other-number")).json()["events"] == 0
    assert (
        rows(environment, "select count(*) n from luma.inbox where company_id=%s", environment["company"])[0][
            "n"
        ]
        == 2
    )


def test_redelivered_events_are_stored_once_and_processed_once(environment, graph):
    """Meta retries the same payload; one inbox row, one message and one agent job result."""
    payload = envelope(messages=[text("Please quote 3 DL-001.", wamid="wamid.same")])
    first, second = deliver_webhook(payload).json(), deliver_webhook(payload).json()
    assert (first["new"], second["new"]) == (1, 0)
    drain()
    drain()
    conversation = conversation_for(environment)
    assert conversation["customer_name"] == "Synthetic Customer" and conversation["recipient"] == SENDER
    messages = rows(environment, "select * from luma.messages where conversation_id=%s", conversation["id"])
    assert [m["provider_id"] for m in messages] == ["wamid.same"]
    jobs = rows(environment, "select * from luma.jobs where conversation_id=%s", conversation["id"])
    assert [j["kind"] for j in jobs] == ["agent"]


def test_unlisted_sender_is_ignored_and_creates_nothing(environment, graph):
    """The test allowlist gates ingress: an unknown number never creates a conversation or job."""
    deliver_webhook(envelope(messages=[text("3 DL-001", sender="15559999999")]))
    drain()
    assert (
        rows(
            environment,
            "select count(*) n from luma.conversations where company_id=%s and channel='whatsapp'",
            environment["company"],
        )[0]["n"]
        == 0
    )
    [inbox] = rows(environment, "select * from luma.inbox where company_id=%s", environment["company"])
    assert (inbox["status"], inbox["error_code"]) == ("ignored", "sender_not_allowed")


def test_second_message_extends_the_same_conversation_and_supersedes_open_work(environment, graph):
    """A later message reuses the thread; queued automated replies are blocked as a customer revision."""
    cid = start(environment, graph)
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute(
            "insert into luma.outbox(id,company_id,conversation_id,kind,payload,action_key) values(%s,%s,%s,'reply',%s,%s)",
            (uuid4(), environment["company"], cid, json.dumps({"text": "stale question"}), f"k:{uuid4()}"),
        )
    deliver_webhook(envelope(messages=[text("Actually 5 DL-002")]))
    drain()
    assert str(conversation_for(environment)["id"]) == cid
    outbox = rows(environment, "select status,error_code from luma.outbox where conversation_id=%s", cid)
    assert (outbox[0]["status"], outbox[0]["error_code"]) == ("blocked", "customer_revision")
    assert (
        len(
            rows(
                environment, "select 1 from luma.messages where conversation_id=%s and actor='customer'", cid
            )
        )
        == 2
    )


def test_inbound_voice_is_fetched_safely_and_enters_the_media_pipeline(environment, graph):
    """An allowlisted voice note is stored privately and queued for transcription, with the bearer only on Meta hosts."""
    graph.media_bytes = wav_bytes()
    graph.media_meta = {
        "url": "https://lookaside.fbsbx.com/m/1",
        "mime_type": "audio/wav",
        "file_size": len(graph.media_bytes),
    }
    event = {
        "from": SENDER,
        "id": "wamid.voice",
        "type": "audio",
        "audio": {"id": "1234567890", "mime_type": "audio/wav"},
    }
    deliver_webhook(envelope(messages=[event]))
    drain()
    cid = conversation_for(environment)["id"]
    [media] = rows(environment, "select * from luma.media where conversation_id=%s", cid)
    environment["files"].append(media["original_path"])
    assert media["kind"] == "audio" and media["status"] == "queued"
    assert [
        j["kind"] for j in rows(environment, "select kind from luma.jobs where conversation_id=%s", cid)
    ] == ["transcribe"]
    assert all(r.headers["authorization"] == "Bearer graph-bearer-token-for-tests" for r in graph.requests)


@pytest.mark.parametrize(
    "meta",
    [
        {"url": "https://attacker.example/steal", "mime_type": "audio/wav", "file_size": 10},
        {"url": "http://lookaside.fbsbx.com/m/1", "mime_type": "audio/wav", "file_size": 10},
        {"url": "https://lookaside.fbsbx.com/m/1", "mime_type": "application/x-msdownload", "file_size": 10},
        {"url": "https://lookaside.fbsbx.com/m/1", "mime_type": "audio/wav", "file_size": 11 * 1024 * 1024},
    ],
    ids=["foreign-host", "plain-http", "wrong-type", "declared-oversize"],
)
def test_hostile_media_metadata_is_refused_without_fetching_or_storing(environment, graph, meta):
    """The token is never sent to a foreign host; refused media yields a fixed notice and no stored object."""
    graph.media_meta = meta
    graph.media_bytes = b"data"
    event = {
        "from": SENDER,
        "id": "wamid.bad",
        "type": "audio",
        "audio": {"id": "42", "mime_type": "audio/wav"},
    }
    deliver_webhook(envelope(messages=[event]))
    drain()
    cid = conversation_for(environment)["id"]
    assert rows(environment, "select 1 from luma.media where conversation_id=%s", cid) == []
    assert not [r for r in graph.requests if r.url.host not in ("graph.facebook.com",)]
    [notice] = rows(environment, "select payload from luma.outbox where conversation_id=%s", cid)
    assert notice["payload"]["text"].startswith("That attachment could not be accepted")


def test_streamed_oversize_and_redirect_are_refused(environment, graph):
    """A body larger than its declared size, or a redirect, is rejected during download."""
    graph.media_bytes = b"x" * (10 * 1024 * 1024 + 1)
    graph.media_meta = {"url": "https://lookaside.fbsbx.com/m/1", "mime_type": "audio/wav"}
    event = {
        "from": SENDER,
        "id": "wamid.big",
        "type": "audio",
        "audio": {"id": "7", "mime_type": "audio/wav"},
    }
    deliver_webhook(envelope(messages=[event]))
    drain()
    graph.media_bytes, graph.media_status = b"", 302
    event = {
        "from": SENDER,
        "id": "wamid.redir",
        "type": "audio",
        "audio": {"id": "8", "mime_type": "audio/wav"},
    }
    deliver_webhook(envelope(messages=[event]))
    drain()
    cid = conversation_for(environment)["id"]
    assert rows(environment, "select 1 from luma.media where conversation_id=%s", cid) == []
    assert len(rows(environment, "select 1 from luma.outbox where conversation_id=%s", cid)) == 2


def test_unsupported_message_types_get_one_fixed_notice(environment, graph):
    """Stickers and other types are recorded as a system note and answered with fixed wording only."""
    deliver_webhook(envelope(messages=[{"from": SENDER, "id": "wamid.sticker", "type": "sticker"}]))
    drain()
    cid = conversation_for(environment)["id"]
    [notice] = rows(environment, "select payload from luma.outbox where conversation_id=%s", cid)
    assert notice["payload"]["text"].startswith("Please send your request as text")


def queue_reply(env, cid, text_="Which colour temperature?"):
    """Queue an agent reply intent directly, as the graph's clarification node does."""
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "insert into luma.outbox(id,company_id,conversation_id,kind,payload,action_key) values(%s,%s,%s,'reply',%s,%s)",
            (uuid4(), env["company"], cid, json.dumps({"text": text_}), f"k:{uuid4()}"),
        )


def outbox(env, cid):
    """Return this conversation's outbox rows, oldest first."""
    return rows(env, "select * from luma.outbox where conversation_id=%s order by created_at", cid)


def test_text_reply_is_submitted_once_with_the_provider_id_recorded(environment, graph):
    """An authorized reply is sent through the Graph API exactly once and stored as submitted, not delivered."""
    cid = start(environment, graph)
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute("update luma.outbox set status='blocked' where conversation_id=%s", (cid,))
    queue_reply(environment, cid)
    assert deliver_one(environment["company"]) is True
    assert deliver_one(environment["company"]) is False
    [request] = graph.sent()
    body = json.loads(request.content)
    assert (body["to"], body["type"], body["text"]["body"]) == (SENDER, "text", "Which colour temperature?")
    assert request.headers["authorization"] == "Bearer graph-bearer-token-for-tests"
    [row] = [r for r in outbox(environment, cid) if r["status"] != "blocked"]
    assert row["status"] == "submitted" and row["provider_id"].startswith("wamid.")
    assert [
        m["provider_id"]
        for m in rows(
            environment,
            "select provider_id from luma.messages where actor='assistant' and conversation_id=%s",
            cid,
        )
    ] == [row["provider_id"]]


@pytest.mark.parametrize(
    ("failure", "status", "code"),
    [
        (httpx.ReadTimeout("slow"), "unknown", "transport_error"),
        (httpx.Response(500, json={}), "unknown", "http_500"),
        (httpx.Response(400, json={"error": {"code": 131047}}), "failed", "131047"),
        (httpx.ConnectError("down"), "failed", "connect_error"),
    ],
    ids=["timeout", "server-error", "rejected", "unreachable"],
)
def test_uncertain_and_failed_submissions_are_recorded_and_never_retried(
    environment, graph, failure, status, code
):
    """A timeout or 5xx is `unknown`, a definite 4xx or unreachable host is `failed`, and nothing is sent twice."""
    cid = start(environment, graph)
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute("update luma.outbox set status='blocked' where conversation_id=%s", (cid,))
    queue_reply(environment, cid)
    graph.send_error = failure
    assert deliver_one(environment["company"]) is True
    assert deliver_one(environment["company"]) is False
    assert len(graph.sent()) == 1
    [row] = [r for r in outbox(environment, cid) if r["status"] != "blocked"]
    assert (row["status"], row["error_code"], row["provider_id"]) == (status, code, None)
    assert (
        rows(environment, "select 1 from luma.messages where actor='assistant' and conversation_id=%s", cid)
        == []
    )


def test_gates_block_without_calling_meta(environment, graph, monkeypatch):
    """Disabled live mode, a recipient outside the allowlist, a closed 24-hour window and takeover all block."""
    cid = start(environment, graph)
    for case in ("disabled", "recipient", "window", "takeover"):
        with psycopg.connect(environment["dsn"]) as conn:
            conn.execute(
                "update luma.outbox set status='blocked' where conversation_id=%s and status='queued'", (cid,)
            )
            conn.execute("update luma.conversations set last_customer_at=now() where id=%s", (cid,))
        monkeypatch.setenv("ENABLE_LIVE_WHATSAPP", "false" if case == "disabled" else "true")
        monkeypatch.setenv("WHATSAPP_TEST_RECIPIENTS", "15550000000" if case == "recipient" else SENDER)
        settings.cache_clear()
        if case == "window":
            with psycopg.connect(environment["dsn"]) as conn:
                conn.execute(
                    "update luma.conversations set last_customer_at=now()-interval '25 hours' where id=%s",
                    (cid,),
                )
        if case == "takeover":
            with psycopg.connect(environment["dsn"]) as conn:
                conn.execute("update luma.conversations set owner='staff' where id=%s", (cid,))
        queue_reply(environment, cid)
        assert deliver_one(environment["company"]) is True
        newest = outbox(environment, cid)[-1]
        assert newest["status"] == "blocked", case
        assert (
            newest["error_code"]
            == {
                "disabled": "live_adapter_not_enabled",
                "recipient": "recipient_not_allowed",
                "window": "outside_service_window",
                "takeover": "dispatch_revalidation",
            }[case]
        )
    assert graph.sent() == []


def test_receipts_advance_monotonically_and_reconcile_unknown(environment, graph):
    """sent/delivered/read only move forward; late duplicates are harmless; a failure after delivery is ignored."""
    cid = start(environment, graph)
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute("update luma.outbox set status='blocked' where conversation_id=%s", (cid,))
    queue_reply(environment, cid)
    deliver_one(environment["company"])
    [row] = [r for r in outbox(environment, cid) if r["status"] == "submitted"]
    wamid = row["provider_id"]

    def receipt(state, code=None):
        """Deliver one status webhook and process it."""
        status = {"id": wamid, "status": state}
        if code:
            status["errors"] = [{"code": code}]
        assert deliver_webhook(envelope(statuses=[status])).status_code == 200
        drain()
        return [r for r in outbox(environment, cid) if r["provider_id"] == wamid][0]["status"]

    assert receipt("read") == "read"
    assert receipt("delivered") == "read"  # an older receipt never regresses state
    assert receipt("sent") == "read"
    assert receipt("failed", "131000") == "read"  # a failure cannot overwrite a read message
    unknown_id = f"wamid.{uuid4().hex}"
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute(
            "insert into luma.outbox(id,company_id,conversation_id,kind,payload,status,provider_id,action_key) values(%s,%s,%s,'reply',%s,'unknown',%s,%s)",
            (uuid4(), environment["company"], cid, json.dumps({"text": "x"}), unknown_id, f"k:{uuid4()}"),
        )
    deliver_webhook(envelope(statuses=[{"id": unknown_id, "status": "delivered"}]))
    drain()
    assert [r for r in outbox(environment, cid) if r["provider_id"] == unknown_id][0]["status"] == "delivered"


def test_receipt_for_a_message_not_yet_recorded_is_retried_then_applied(environment, graph):
    """A receipt that races ahead of the send record waits, then applies once the message id exists."""
    cid = start(environment, graph)
    wamid = f"wamid.{uuid4().hex}"
    deliver_webhook(envelope(statuses=[{"id": wamid, "status": "delivered"}]))
    drain()
    [pending] = rows(
        environment, "select * from luma.inbox where kind='status' and company_id=%s", environment["company"]
    )
    assert (pending["status"], pending["error_code"]) == ("queued", "unknown_message")
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute(
            "insert into luma.outbox(id,company_id,conversation_id,kind,payload,status,provider_id,action_key) values(%s,%s,%s,'reply',%s,'submitted',%s,%s)",
            (uuid4(), environment["company"], cid, json.dumps({"text": "x"}), wamid, f"k:{uuid4()}"),
        )
        conn.execute(
            "update luma.inbox set lease_until=null where kind='status' and company_id=%s",
            (environment["company"],),
        )
    drain()
    assert [r for r in outbox(environment, cid) if r["provider_id"] == wamid][0]["status"] == "delivered"


def test_approved_quotation_is_sent_as_the_exact_canonical_pdf(environment, graph):
    """An approved, fresh quotation uploads the stored PDF bytes unchanged and sends one document message."""
    cid = start(environment, graph)
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute(
            "update luma.snapshots set source='google_sheets',observed_at=now() where company_id=%s",
            (environment["company"],),
        )
        conn.execute("update luma.outbox set status='blocked' where conversation_id=%s", (cid,))
    quote = make_draft(environment, cid)
    environment["files"].append(f"{environment['company']}/quotes/{quote['id']}.pdf")
    assert (
        post(
            environment, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 200
    )
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute(
            "update luma.snapshots set observed_at=now() where company_id=%s", (environment["company"],)
        )
    deliver_one(environment["company"])
    [upload] = [r for r in graph.requests if r.url.path.endswith("/media")]
    staff_pdf = (
        environment["api"].get(f"/api/quotes/{quote['id']}/pdf", headers=environment["headers"]).content
    )
    # The uploaded multipart part carries the stored PDF bytes unchanged.
    assert staff_pdf in upload.content
    [send] = graph.sent()
    document = json.loads(send.content)["document"]
    assert (
        document["id"] == "99887766"
        and document["filename"].endswith("-r1.pdf")
        and "Total USD" in document["caption"]
    )
    [row] = [r for r in outbox(environment, cid) if r["kind"] == "quotation"]
    assert row["status"] == "submitted" and get_detail(environment, cid)["conversation"]["status"] == "quoted"
