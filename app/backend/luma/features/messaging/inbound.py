"""Worker-side processing of persisted WhatsApp, Telegram and email events: inbound messages and receipts.

Each `luma.inbox` row is claimed under a two-minute lease, processed and finished as `done`,
`ignored` (a deliberate non-action such as a sender outside the test allowlist) or `failed`.
Transient problems (rate limit, unreachable provider, a receipt that arrives before the send was
recorded) requeue with a short delay up to five attempts. Provider payloads and customer text
are never logged; only opaque codes are stored.

Authority: a sender is trusted only if it is on its channel's allowlist (`WHATSAPP_TEST_RECIPIENTS`
numbers, `TELEGRAM_ALLOWED_USERS` user ids, or `EMAIL_ALLOWED_SENDERS` addresses that Gmail also
authenticated; an empty list admits nobody). Events carry a
`channel` field (absent means WhatsApp), which picks the allowlist and the conversation channel. Inbound content can create or extend a customer conversation and queue
the same agent job as any other customer message; it can never approve, price, send or change
ownership. Media is fetched only through the restricted client of the provider that
received it (`provider.fetch_media`: Graph, or Twilio for D43 events) and then passes the same
sandboxed decoder and written-confirmation gate as an uploaded file.
"""

from uuid import uuid4

from psycopg.types.json import Jsonb

from luma.core.audit import audit
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.participation import accept_customer_text
from luma.features.conversations.repository import conversation
from luma.features.conversations.service import add_message
from luma.features.media.intake import store_media

from .allowlist import allowed
from .errors import ProviderError
from .provider import fetch_media

MAX_ATTEMPTS = 5
RETRY_SECONDS = 30
AUDIO_TYPES = ("audio/ogg", "audio/mpeg", "audio/mp4", "audio/aac", "audio/amr", "audio/wav", "audio/x-wav")
IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp")
UNSUPPORTED = "Please send your request as text, a voice note or a product-label photo."
GREETING = (
    "Hello! Send your lighting request as text, a voice note or a product-label photo, "
    "and our sales team will prepare a quotation."
)
REJECTED = "That attachment could not be accepted. Please send your request as text."
RANK = {"queued": 0, "submitting": 0, "unknown": 0, "submitted": 1, "delivered": 2, "read": 3}
STATUS_TO_OUTBOX = {"sent": "submitted", "delivered": "delivered", "read": "read"}


class Retry(Exception):
    """Signal a transient condition; the row is requeued after a delay rather than failed."""

    def __init__(self, code: str):
        """Keep only the opaque reason code."""
        super().__init__(code)
        self.code = code


def claim():
    """Lease the oldest runnable inbox row; expired leases are retried or failed at the attempt cap."""
    with database(worker=True) as conn:
        conn.execute("select pg_advisory_xact_lock(hashtextextended('luma:inbox',0))")
        conn.execute(
            """update luma.inbox set status='failed',error_code='attempts_exhausted',updated_at=now()
            where status in ('queued','processing') and attempts>=%s and (lease_until is null or lease_until<now())""",
            (MAX_ATTEMPTS,),
        )
        return conn.execute(
            """update luma.inbox set status='processing',attempts=attempts+1,lease_until=now()+interval '2 minutes',
            updated_at=now() where provider_id=(select provider_id from luma.inbox
            where status in ('queued','processing') and (lease_until is null or lease_until<now())
            order by created_at for update skip locked limit 1) returning *"""
        ).fetchone()


def finish(row, status: str, code: str | None = None, delay: int = 0) -> None:
    """Record the outcome; a delay requeues the row for a later attempt instead of finishing it."""
    with database(worker=True) as conn:
        if delay:
            conn.execute(
                """update luma.inbox set status='queued',error_code=%s,lease_until=now()+make_interval(secs => %s),
                updated_at=now() where provider_id=%s""",
                (code, delay, row["provider_id"]),
            )
        else:
            conn.execute(
                "update luma.inbox set status=%s,error_code=%s,lease_until=null,updated_at=now() where provider_id=%s",
                (status, code, row["provider_id"]),
            )


def open_conversation(conn, company, sender: str, name: str, channel: str = "whatsapp"):
    """Return the locked conversation for this sender on `channel`, creating it once under a per-sender lock."""
    conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (f"{channel}:{company}:{sender}",))
    found = conn.execute(
        """select id from luma.conversations where company_id=%s and channel=%s and recipient=%s
        order by created_at limit 1""",
        (company, channel, sender),
    ).fetchone()
    cid = found["id"] if found else uuid4()
    if not found:
        conn.execute(
            """insert into luma.conversations(id,company_id,customer_name,customer_company,recipient,channel)
            values(%s,%s,%s,'',%s,%s)""",
            (cid, company, name or sender, sender, channel),
        )
        audit(conn, company, channel, "conversation.created", cid)
    return conversation(conn, company, cid, lock=True)


def queue_notice(conn, company, current, text: str, key: str) -> None:
    """Queue one fixed, customer-visible notice, only while the agent (not staff) owns the conversation."""
    if current["owner"] != "agent":
        return
    conn.execute(
        """insert into luma.outbox(id,company_id,conversation_id,kind,payload,action_key)
        values(%s,%s,%s,'reply',%s,%s) on conflict(action_key) do nothing""",
        (uuid4(), company, current["id"], Jsonb({"text": text}), key),
    )


def handle_message(row) -> tuple[str, str | None]:
    """Apply one inbound customer message; returns the inbox outcome and an optional opaque code."""
    event, company = row["payload"], row["company_id"]
    channel = event.get("channel", "whatsapp")
    if channel == "email" and not event.get("authenticated"):
        # From is easy to fake; Gmail's own authentication result must vouch for it (D47).
        return "ignored", "sender_unauthenticated"
    if event["from"] not in allowed(channel):
        return "ignored", "sender_not_allowed"
    kind = event["type"]
    data = None
    if kind in ("audio", "image"):
        limit = 10 if kind == "audio" else 5
        try:
            data, _ = fetch_media(event, limit * 1024 * 1024, AUDIO_TYPES if kind == "audio" else IMAGE_TYPES)
        except ProviderError as error:
            if error.kind == "rejected":
                data = None
            else:
                raise Retry(error.code) from None
    with database(worker=True) as conn:
        current = open_conversation(conn, company, event["from"], event.get("name", ""), channel)
        if kind == "text":
            if not event.get("text", "").strip():
                return "ignored", "empty_text"
            if channel == "telegram" and event["text"].strip().split()[0].split("@")[0] == "/start":
                queue_notice(conn, company, current, GREETING, f"inbound-notice:{event['id']}")
                return "done", None
            if channel == "email" and event.get("attachments"):
                add_message(conn, company, current["id"], "system", "Email attachments are not processed yet.")
            try:
                accept_customer_text(conn, company, current, event["text"], provider_id=event["id"])
            except DomainError as error:
                if error.status == 429:
                    raise Retry("rate_limited") from None
                raise
        elif kind in ("audio", "image"):
            try:
                if data is None:
                    raise DomainError("Attachment refused.", 422)
                store_media(conn, company, channel, current["id"], data, kind=kind, provider_id=event["id"])
            except DomainError as error:
                if error.status == 429:
                    raise Retry("rate_limited") from None
                add_message(conn, company, current["id"], "system", "A customer attachment was refused.")
                queue_notice(conn, company, current, REJECTED, f"inbound-notice:{event['id']}")
        else:
            add_message(conn, company, current["id"], "system", "An unsupported message type was received.")
            queue_notice(conn, company, current, UNSUPPORTED, f"inbound-notice:{event['id']}")
    return "done", None


def apply_status(row) -> tuple[str, str | None]:
    """Apply one delivery receipt monotonically; late or duplicate receipts never move a state backwards.

    `sent` -> submitted, `delivered`, `read` only advance. `failed` applies only to a send
    that is still unconfirmed (submitting/unknown/submitted). A receipt for an unknown
    message id is retried, because it can race ahead of the sender recording the message id.
    A receipt is evidence about a send; it never creates, approves or retries one.
    """
    event, company = row["payload"], row["company_id"]
    with database(worker=True) as conn:
        item = conn.execute(
            "select * from luma.outbox where company_id=%s and provider_id=%s for update",
            (company, event["id"]),
        ).fetchone()
        if not item:
            raise Retry("unknown_message")
        if event["status"] == "failed":
            if item["status"] in ("submitting", "unknown", "submitted"):
                conn.execute(
                    "update luma.outbox set status='failed',error_code=%s,updated_at=now() where id=%s",
                    (event["code"] or "provider_failed", item["id"]),
                )
                audit(conn, company, "whatsapp", "delivery.failed", item["id"])
            return "done", None
        new = STATUS_TO_OUTBOX[event["status"]]
        if RANK.get(item["status"], -1) < RANK[new] and item["status"] not in ("failed", "blocked", "local_delivered"):
            conn.execute("update luma.outbox set status=%s,error_code=null,updated_at=now() where id=%s", (new, item["id"]))
            audit(conn, company, "whatsapp", f"delivery.{new}", item["id"])
    return "done", None


def process_next() -> bool:
    """Process at most one inbox row; True when a row was claimed (whatever its outcome)."""
    row = claim()
    if not row:
        return False
    try:
        outcome, code = handle_message(row) if row["kind"] == "message" else apply_status(row)
        finish(row, outcome, code)
    except Retry as retry:
        finish(row, "failed", retry.code, delay=RETRY_SECONDS)
    except DomainError as error:
        finish(row, "failed", f"http_{error.status}"[:40])
    except Exception as error:
        finish(row, "failed", type(error).__name__[:40])
    return True
