"""Gmail channel (D47) against real PostgreSQL and Storage with a Python stand-in for `gas/Mail.gs`.

The stand-in signs envelopes exactly as Apps Script does (shared `signedExportPost_`). This proves
the gateway, inbox, worker and pull-dispatch rules. It does NOT prove that Apps Script reads Gmail,
that Gmail sends the reply or that a tunnel reaches the gateway. Label: local-substitute.
"""

import base64
import hashlib
import hmac
import json
import time
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.features.messaging import inbound
from luma.google_gateway import app
from luma_agent.runtime.delivery import deliver_one
from psycopg.rows import dict_row
from test_manual_workflow import get_detail, make_draft, post

SHEET = "synthetic-workbook"
CUSTOMER = "customer@example.com"
AUTH = (
    "mx.google.com; dkim=pass header.i=@example.com header.s=s1 header.b=abc; "
    "spf=pass smtp.mailfrom=customer@example.com; dmarc=pass (p=NONE) header.from=example.com"
)


class Script:
    """Minimal Apps Script substitute that signs and posts mail envelopes to the real gateway."""

    def __init__(self, company, secret):
        """Remember the bound company and shared secret."""
        self.company, self.secret = str(company), secret

    def send(self, path, event, valid=True, **fields):
        """Sign exact JSON bytes and post them; `valid=False` forges the signature."""
        envelope = {
            "schema_version": 1, "company_id": self.company, "spreadsheet_id": SHEET,
            "timestamp": int(time.time()), "nonce": str(uuid4()), "event": event, **fields,
        }
        body = json.dumps(envelope).encode()
        signature = hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest() if valid else "0" * 64
        with TestClient(app) as client:
            return client.post(path, content=body, headers={"X-Luma-Signature": signature})

    def push(self, *mails, valid=True):
        """Push mails to the inbound endpoint."""
        return self.send("/callbacks/google/mail/inbound", "gmail_messages", valid, messages=list(mails))

    def claim(self):
        """Claim the next queued reply."""
        return self.send("/callbacks/google/mail/claim", "gmail_send_claim")

    def receipt(self, mail, outcome="sent", **fields):
        """Report one claimed reply."""
        extra = {"gmail_message_id": "18d0000000000abc"} if outcome == "sent" else {"error_code": "send_error"}
        return self.send(
            "/callbacks/google/mail/receipt", "gmail_send_receipt",
            dispatch_id=mail["dispatch_id"], claim_token=mail["claim_token"], outcome=outcome, **{**extra, **fields},
        )


@pytest.fixture
def script(environment, monkeypatch):
    """Configure the gateway, allowlist and live switch for the isolated company."""
    monkeypatch.setenv("GOOGLE_COMPANY_ID", str(environment["company"]))
    monkeypatch.setenv("GOOGLE_SHEET_ID", SHEET)
    monkeypatch.setenv("GOOGLE_CALLBACK_SECRET", "test-only-mail-key-" + "z" * 32)
    monkeypatch.setenv("EMAIL_ALLOWED_SENDERS", CUSTOMER)
    monkeypatch.setenv("ENABLE_LIVE_EMAIL", "true")
    settings.cache_clear()
    yield Script(environment["company"], settings().google_callback_secret.get_secret_value())
    settings.cache_clear()


def mail(body="i want 5 dl-001", sender=f"Customer <{CUSTOMER}>", auth=AUTH, attachments=0, subject="Quote"):
    """Build one Gmail message as Apps Script would read it, with a fresh message id."""
    return {
        "message_id": uuid4().hex[:16], "thread_id": uuid4().hex[:16], "from_header": sender,
        "reply_to": "", "subject": subject, "date_ms": int(time.time() * 1000), "auth_results": auth,
        "body": body, "attachments": attachments,
    }


def process(env, message_id):
    """Run the inbox worker until this mail is finished; return its inbox row."""
    for _ in range(50):
        with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
            row = conn.execute("select * from luma.inbox where provider_id=%s", (f"gm:{message_id}",)).fetchone()
        if row["status"] not in ("queued", "processing"):
            return row
        inbound.process_next()
    pytest.fail("The mail was not processed.")


def conversation_for(env, address=CUSTOMER):
    """Return this tenant's email conversation for an address, or None."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        return conn.execute(
            "select * from luma.conversations where company_id=%s and channel='email' and recipient=%s",
            (env["company"], address),
        ).fetchone()


def rows(env, sql, *args):
    """Run one read query for this test."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        return conn.execute(sql, args).fetchall()


def test_signed_push_is_stored_once_and_opens_an_email_conversation(environment, script):
    """A pushed mail is stored, deduplicated, stripped of quoted history and becomes a customer message."""
    env = environment
    first = mail(body="i want 5 dl-001\n\nOn Sat, Nov 7, 2026 at 5:00 PM Luma <me@example.org> wrote:\n> old")
    response = script.push(first)
    assert response.status_code == 200 and response.json() == {"stored": [first["message_id"]]}
    assert script.push(first).status_code == 200
    assert len(rows(env, "select 1 from luma.inbox where provider_id=%s", f"gm:{first['message_id']}")) == 1
    assert process(env, first["message_id"])["status"] == "done"
    current = conversation_for(env)
    assert current and current["owner"] == "agent"
    messages = rows(env, "select actor,body from luma.messages where conversation_id=%s", current["id"])
    assert [(m["actor"], m["body"]) for m in messages] == [("customer", "i want 5 dl-001")]
    assert rows(env, "select 1 from luma.jobs where conversation_id=%s and status='queued'", current["id"])


def test_forged_or_unconfigured_push_is_refused(environment, script, monkeypatch):
    """A wrong signature is 401; without the Google secret the endpoint answers 503."""
    assert script.push(mail(), valid=False).status_code == 401
    monkeypatch.setenv("GOOGLE_CALLBACK_SECRET", "")
    settings.cache_clear()
    assert script.push(mail()).status_code == 503


@pytest.mark.parametrize("sender,auth,code", [
    (f"Customer <{CUSTOMER}>", "", "sender_unauthenticated"),
    (f"Customer <{CUSTOMER}>", "mx.google.com; dmarc=pass header.from=evil.example", "sender_unauthenticated"),
    ("Other <other@example.com>", AUTH, "sender_not_allowed"),
])
def test_unauthenticated_or_unlisted_sender_is_ignored(environment, script, sender, auth, code):
    """A faked or unlisted sender is stored as ignored and never opens a conversation."""
    env = environment
    item = mail(sender=sender, auth=auth)
    assert script.push(item).status_code == 200
    row = process(env, item["message_id"])
    assert (row["status"], row["error_code"]) == ("ignored", code)
    assert conversation_for(env, "other@example.com") is None
    assert code != "sender_unauthenticated" or conversation_for(env) is None


def queued_notice(env, script):
    """Push an attachments-only mail (fixed notice) and dispatch its reply; return (conversation, inbound id)."""
    item = mail(body="", subject="", attachments=1)
    assert script.push(item).status_code == 200
    process(env, item["message_id"])
    current = conversation_for(env)
    assert deliver_one(env["company"]) is True
    return current, item["message_id"]


def test_reply_is_claimed_once_sent_in_thread_and_recorded(environment, script):
    """The gated reply waits for Apps Script, is claimed once, and a sent receipt records it."""
    env = environment
    current, inbound_id = queued_notice(env, script)
    [outbox] = rows(env, "select * from luma.outbox where conversation_id=%s", current["id"])
    [dispatch] = rows(env, "select * from luma.email_dispatch where outbox_id=%s", outbox["id"])
    assert (outbox["status"], dispatch["status"]) == ("submitting", "waiting")
    claimed = script.claim().json()["mail"]
    assert claimed["to"] == CUSTOMER and claimed["reply_message_id"] == inbound_id
    assert claimed["subject"] == "Re: Your lighting request" and claimed["attachment"] is None  # empty subject
    assert claimed["body"] == inbound.UNSUPPORTED
    assert script.claim().json() == {"mail": None}
    assert script.receipt(claimed).json() == {"status": "sent"}
    [outbox] = rows(env, "select * from luma.outbox where id=%s", outbox["id"])
    assert (outbox["status"], outbox["provider_id"]) == ("submitted", f"gm-out:{outbox['id']}")
    sent = rows(env, "select actor,body from luma.messages where conversation_id=%s and actor='assistant'", current["id"])
    assert [m["body"] for m in sent] == [inbound.UNSUPPORTED]
    assert script.receipt(claimed).status_code == 200


def test_expired_claim_becomes_unknown_and_is_never_offered_again(environment, script):
    """A claim without a receipt may have been sent, so it turns unknown instead of being resent."""
    env = environment
    current, _ = queued_notice(env, script)
    claimed = script.claim().json()["mail"]
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "update luma.email_dispatch set lease_until=now()-interval '1 second' where outbox_id=%s",
            (claimed["dispatch_id"],),
        )
    assert script.claim().json() == {"mail": None}
    [dispatch] = rows(env, "select status from luma.email_dispatch where outbox_id=%s", claimed["dispatch_id"])
    [outbox] = rows(env, "select status,error_code from luma.outbox where id=%s", claimed["dispatch_id"])
    assert dispatch["status"] == "unknown" and (outbox["status"], outbox["error_code"]) == ("unknown", "mail_receipt_missing")
    assert script.receipt(claimed).status_code == 409


def test_failed_receipt_fails_the_outbox(environment, script):
    """A send error reported by Apps Script is a definite failure."""
    env = environment
    queued_notice(env, script)
    claimed = script.claim().json()["mail"]
    assert script.receipt(claimed, outcome="failed").json() == {"status": "failed"}
    [outbox] = rows(env, "select status,error_code from luma.outbox where id=%s", claimed["dispatch_id"])
    assert (outbox["status"], outbox["error_code"]) == ("failed", "gmail_send_error")


def test_live_switch_off_blocks_before_any_dispatch(environment, script, monkeypatch):
    """With ENABLE_LIVE_EMAIL off the reply is blocked and nothing is offered to Apps Script."""
    env = environment
    monkeypatch.setenv("ENABLE_LIVE_EMAIL", "false")
    settings.cache_clear()
    current, _ = queued_notice(env, script)
    [outbox] = rows(env, "select status,error_code from luma.outbox where conversation_id=%s", current["id"])
    assert (outbox["status"], outbox["error_code"]) == ("blocked", "live_adapter_not_enabled")
    assert script.claim().json() == {"mail": None}


def test_approved_quotation_is_claimed_with_the_exact_canonical_pdf(environment, script):
    """An approved quotation's reply carries the stored PDF bytes and their digest."""
    env = environment
    item = mail()
    script.push(item)
    process(env, item["message_id"])
    current = conversation_for(env)
    cid = str(current["id"])
    fresh = "update luma.snapshots set source='google_sheets',observed_at=now() where company_id=%s"
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(fresh, (env["company"],))
    quote = make_draft(env, cid)
    env["files"].append(f"{env['company']}/quotes/{quote['id']}.pdf")
    approved = post(env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"})
    assert approved.status_code == 200, approved.text
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(fresh, (env["company"],))
    while deliver_one(env["company"]):
        pass
    claimed = script.claim().json()["mail"]
    pdf = base64.b64decode(claimed["attachment"]["pdf_base64"])
    staff = env["api"].get(f"/api/quotes/{quote['id']}/pdf", headers=env["headers"]).content
    assert pdf == staff and claimed["attachment"]["sha256"] == hashlib.sha256(pdf).hexdigest()
    assert claimed["body"].startswith("Quotation ") and get_detail(env, cid)["quote"]["status"] == "approved"
