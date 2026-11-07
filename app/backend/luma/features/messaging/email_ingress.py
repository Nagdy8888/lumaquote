"""Signed Gmail push from Apps Script into the durable inbox (decision D47).

Apps Script (`gas/Mail.gs`) reads mails under the configured Gmail label and POSTs batches of at
most ten to `/callbacks/google/mail/inbound`, signed with the same HMAC envelope as the supplier and
Drive-export callbacks (company, workbook, five-minute timestamp, single-use nonce). Each mail is
reduced to a channel event and stored in `luma.inbox` under `gm:<gmail message id>` before the
response, so Apps Script moves its cursor only after the mails are persisted. Repeats are ignored
by that key.

Trust: the envelope proves the mail came through the user's own Apps Script, not who wrote it.
`From` is easy to fake, so a sender counts only when Gmail's own `Authentication-Results` header
(added by `mx.google.com`) shows DMARC, DKIM or SPF passing for the From domain
(`sender_authenticated`), and only when the address is on `EMAIL_ALLOWED_SENDERS`
(`inbound.handle_message`). Quoted earlier messages are cut (`strip_quoted`) so a reply such as
"yes" reaches the agent as "yes". Attachments are not processed in this version.
"""

import re
from email.utils import parseaddr
from typing import Literal

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field

from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.google_sync.exports import ExportEnvelope, record_nonce, verify_envelope

MAX_TEXT = 4000
GMAIL_ID = r"^[0-9a-f]{10,32}$"
ADDRESS = re.compile(r"[^@\s<>]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,63}")
QUOTE_START = (
    re.compile(r"^on\b.{0,300}\bwrote:\s*$", re.IGNORECASE),
    re.compile(r"^-{2,}\s*original message\s*-{2,}", re.IGNORECASE),
    re.compile(r"^_{5,}\s*$"),
    re.compile(r"^في\s.{0,300}كتب.{0,300}:\s*$"),
)


class MailItem(BaseModel):
    """One Gmail message as Apps Script reads it; every field is untrusted customer content."""

    model_config = ConfigDict(extra="forbid")
    message_id: str = Field(pattern=GMAIL_ID)
    thread_id: str = Field(pattern=GMAIL_ID)
    from_header: str = Field(min_length=3, max_length=400)
    reply_to: str = Field(default="", max_length=400)
    subject: str = Field(default="", max_length=300)
    date_ms: int = Field(ge=0)
    auth_results: str = Field(default="", max_length=4000)
    body: str = Field(default="", max_length=20000)
    attachments: int = Field(default=0, ge=0, le=100)


class MailPush(ExportEnvelope):
    """A signed batch of at most ten mails from Apps Script."""

    event: Literal["gmail_messages"]
    messages: list[MailItem] = Field(max_length=10)


def sender_address(header: str) -> str:
    """Return the lowercase address from a From or Reply-To header, or '' when it is not one address."""
    address = parseaddr(header)[1].strip().lower()
    return address if ADDRESS.fullmatch(address) else ""


def sender_authenticated(results: str, address: str) -> bool:
    """True when Gmail's own Authentication-Results show the From domain passing DMARC, DKIM or SPF.

    Only a header whose authserv-id is `mx.google.com` counts. DMARC must name the From domain in
    `header.from`; DKIM must sign for it (`header.i=@domain` or `header.d=domain`); SPF must pass
    for an envelope sender in the same domain. Anything else, including an empty header, is False.
    """
    if "@" not in address:
        return False
    domain = re.escape(address.rsplit("@", 1)[1])
    head, _, rest = results.partition(";")
    if head.strip().lower() != "mx.google.com":
        return False
    for clause in rest.lower().split(";"):
        clause = clause.strip()
        if clause.startswith("dmarc=pass") and re.search(rf"header\.from={domain}(?:\s|$)", clause):
            return True
        if clause.startswith("dkim=pass") and re.search(rf"header\.(?:i=@|d=){domain}(?:\s|$)", clause):
            return True
        if clause.startswith("spf=pass") and re.search(rf"smtp\.mailfrom=[^@\s]+@{domain}(?:\s|$)", clause):
            return True
    return False


def strip_quoted(body: str) -> str:
    """Keep only the new text of a reply: stop at a quote header, a `>` line or a `-- ` signature."""
    lines = body.replace("\r\n", "\n").split("\n")
    kept = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        joined = f"{stripped} {lines[index + 1].strip()}" if index + 1 < len(lines) else stripped
        if stripped.startswith(">") or line.rstrip("\n") == "-- ":
            break
        if any(pattern.match(stripped) or pattern.match(joined) for pattern in QUOTE_START):
            break
        kept.append(line)
    return "\n".join(kept).strip()


def reduce_mail(item: MailItem) -> tuple[str, str, dict] | None:
    """Turn one mail into an inbox `(provider_id, kind, event)`, or None when the sender is not an address.

    The text is the new part of the body, or the subject when the body is empty, cut to 4000
    characters. A mail with no text but attachments becomes `unsupported` (fixed notice).
    """
    address = sender_address(item.from_header)
    if not address:
        return None
    text = strip_quoted(item.body)[:MAX_TEXT] or item.subject.strip()[:MAX_TEXT]
    event = {
        "provider": "gmail",
        "channel": "email",
        "id": f"gm:{item.message_id}",
        "message_id": item.message_id,
        "thread_id": item.thread_id,
        "from": address,
        "name": parseaddr(item.from_header)[0].strip()[:120],
        "reply_to": sender_address(item.reply_to),
        "subject": item.subject.strip()[:300],
        "authenticated": sender_authenticated(item.auth_results, address),
        "attachments": item.attachments,
        "type": "text" if text else ("unsupported" if item.attachments else "text"),
        "text": text,
    }
    return event["id"], "message", event


def receive_mail(body: bytes, signature: str) -> dict:
    """Verify one signed batch, store each mail once under the configured company and list the stored ids.

    A replayed envelope with the same bytes returns the same answer without storing again. The
    company comes from the verified envelope binding (`GOOGLE_COMPANY_ID`), never from mail content.
    """
    push = verify_envelope(MailPush, body, signature)
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='10s'")
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (str(push.company_id),))
            record_nonce(conn, push, body)
            stored = []
            for item in push.messages:
                reduced = reduce_mail(item)
                if reduced:
                    provider_id, kind, event = reduced
                    conn.execute(
                        """insert into luma.inbox(provider_id,company_id,payload,kind) values(%s,%s,%s,%s)
                        on conflict(provider_id) do nothing""",
                        (provider_id, push.company_id, Jsonb(event), kind),
                    )
                stored.append(item.message_id)
    except psycopg.Error:
        raise DomainError("Mail storage is unavailable.", 503) from None
    return {"stored": stored}
