# Email channel (Gmail through Apps Script)

This explains the Gmail channel added in decision D47: what it trusts, how a mail moves through it,
what it writes, and what it does and does not prove. It is tested with a Python stand-in for Apps
Script (`tests/integration/test_email.py`, `tests/unit/test_email_ingress.py`) and passed one `live`
round trip on 2026-11-07 (see Tests and evidence). Live sending is off by default
(`ENABLE_LIVE_EMAIL=false`). Setup steps are in [morning actions](../MORNING_ACTIONS.md).

## Why this design

The user asked for customer requests by Gmail as well as Telegram. Decision D10 keeps all Google
access inside the user's own Apps Script (no backend Google login), so Apps Script reads and sends
the mail and talks to the backend through the same signed gateway as the supplier snapshot and the
Drive export. The agent reads only one Gmail label (`LumaQuote` by default) in the user's own
mailbox; a Gmail filter decides which mails get it. Mail outside that label is never read.

## Actors and authority

| Actor | Can | Cannot |
| --- | --- | --- |
| Apps Script (`gas/Mail.gs`, signed with `LUMA_CALLBACK_SECRET`) | push labelled mails; claim and send replies the backend queued; report results | choose the company, read conversations, approve, price, or resend a claimed reply |
| Customer (allowlisted address, Gmail-authenticated) | open or extend an email conversation with text | reach the agent when unauthenticated or not on `EMAIL_ALLOWED_SENDERS`; attachments are not processed |
| Worker | process the inbox, run the agent, gate and queue replies | send mail itself |
| Staff | approve quotations, take over, reply (same rules as other channels) | — |

The company is `GOOGLE_COMPANY_ID`, bound to the signed envelope; nothing in a mail selects a tenant.

## Modules and call flow

| Module | Role |
| --- | --- |
| `gas/Mail.gs` | `pollLumaMail` (push), `sendLumaMail` (claim, send, receipt), `installLumaMail` (two one-minute triggers) |
| `messaging/email_routes.py` | gateway routes `/callbacks/google/mail/inbound`, `/claim`, `/receipt` |
| `messaging/email_ingress.py` | envelope schema, `sender_authenticated`, `strip_quoted`, `reduce_mail`, `receive_mail` |
| `messaging/email_dispatch.py` | `queue` (from the dispatcher), `claim_mail`, `record_mail_receipt`, lease and expiry `sweep` |
| `messaging/inbound.py` | same inbox processing; email adds the authentication check |
| `luma_agent/runtime/delivery.py` | email intents are gated by `outbound.begin`, then queued instead of sent |

```
Customer mail -> Gmail filter adds label LumaQuote
  -> pollLumaMail (every minute): mails newer than the cursor, not from this account, max 5
  -> POST /callbacks/google/mail/inbound (signed) -> luma.inbox 'gm:<message id>' -> cursor moves
  -> inbox worker: Gmail authentication -> allowlist -> email conversation -> agent job
  -> agent reply or approved quotation -> outbox -> dispatcher: outbound.begin gates -> email_dispatch 'waiting'
  -> sendLumaMail (every minute): POST /claim -> reply in the customer's thread (PDF attached) -> POST /receipt
  -> outbox 'submitted' (or 'failed'), assistant message recorded
```

## Inputs and outputs

Push (`gmail_messages`, at most 5 mails from Apps Script, schema allows 10, body at most 256 KiB):
`message_id`, `thread_id` (Gmail hex ids), `from_header`, `reply_to`, `subject`, `date_ms`,
`auth_results` (Gmail's `Authentication-Results` header), `body` (plain text, Apps Script sends at
most 8000 characters), `attachments` (count). The stored event text is the new part of the body
(`strip_quoted` stops at an `On ... wrote:` line, an Arabic `في ... كتب ...:` line, `>` lines, an
`Original Message` divider or a `-- ` signature), else the subject, cut to 4000 characters. A mail
with no text but attachments becomes `unsupported` and gets the fixed notice. When a mail has text and
attachments, the text is processed and a system note records that attachments were not processed.

Claim response: `dispatch_id`, `claim_token`, `to`, `subject` (`Re: ` plus the newest mail's subject
from this sender, or `Re: Your lighting request`), `body`, `reply_message_id`, and for a quotation an
`attachment` with `filename`, `sha256`, `size` and `pdf_base64` (the canonical stored PDF, at most
5 MiB). Apps Script replies in the original thread only when that message's reply address equals
`to`; otherwise it sends a new mail to `to`. It checks the PDF digest before attaching it.

Receipt: `outcome` `sent` (with the Gmail message id when visible) or `failed` with an `error_code`
(`transfer_corrupt`, `send_error`). The outbox provider id is `gm-out:<outbox id>`.

## Sender authentication

`From` can be forged, so a mail counts only when `sender_authenticated` finds, in a header whose
authserv-id is `mx.google.com`, one of: `dmarc=pass` with `header.from=<From domain>`; `dkim=pass`
with `header.i=@<domain>` or `header.d=<domain>`; `spf=pass` with `smtp.mailfrom` in that domain.
Otherwise the inbox row is `ignored` with `sender_unauthenticated`. Then the address must be on
`EMAIL_ALLOWED_SENDERS` (`sender_not_allowed` otherwise). Not verified live: which
`Authentication-Results` occurrence Apps Script's `getHeader` returns when a mail carries several.
Gmail adds its own at the top, and the allowlist still applies.

## State transitions

Inbox rows follow the shared rules (`queued`, `processing`, `done`, `ignored`, `failed`).
`luma.email_dispatch`: `waiting` -> `claimed` -> `sent` or `failed`; `claimed` with an expired
five-minute lease -> `unknown`; `waiting` for 24 hours -> `failed` (`mail_not_collected`); a row whose
outbox left `submitting` -> `failed` (`outbox_changed`). The outbox mirrors these: `submitting` while
waiting or claimed, then `submitted`, `failed` or `unknown`. Email has no delivery or read receipts.
The dispatcher's two-minute stale-`submitting` sweep skips rows that have an email dispatch.

## Database writes and transactions

Migration `20261107020000_email_channel.sql` adds `email` to `conversations_channel_check` and the
`luma.email_dispatch` table (RLS on; staff may read their company's rows, the worker role writes).
`receive_mail` stores a whole batch in one transaction under the company advisory lock after the
nonce check. `queue` runs inside the dispatcher's transaction that marked the outbox `submitting`.
`claim_mail` and `record_mail_receipt` take the company lock; the receipt also takes the conversation
lock before `outbound.record`, the same order the dispatcher uses.

## Idempotency

Inbox key `gm:<Gmail message id>`; a re-pushed mail is ignored. Envelopes are single-use nonces
(identical replays are accepted without new effects). A dispatch row is claimed at most once
(`attempts` 0..1), and an expired claim is never offered again, because Gmail may already have sent
it. Apps Script moves its cursor only after the backend answered 200.

## Limits and cost

Apps Script runs each trigger about once a minute (approximate). All `.gs` files share one script lock
(`LockService.getScriptLock()`): supplier sync (8-11 s on 2026-11-07), mail poll, mail send and Drive export run
one at a time, so a reply can be delayed by up to about one sync. Gmail and Apps Script daily quotas
apply to the user's account (check the current quota page before relying on numbers). Each customer
mail costs the same paid AI call as a Telegram message when paid AI is on.

## External effects and secrets

Mail bodies and addresses are customer data: they are stored in the local database and, when tracing
is on, appear in masked LangSmith traces like other messages (D24). Apps Script logs only HTTP status
codes in Script Properties. The callback secret stays in Script Properties and `.env.local`. The
manifest adds the `https://mail.google.com/` and `userinfo.email` scopes (the second is needed by
`Session.getEffectiveUser`, which tells the script its own address; without it every poll failed), so
the user must re-authorize the script.

## Failures and recovery

| Condition | Result |
| --- | --- |
| Gateway unreachable or not 200 on push | cursor unchanged, next run retries; mails deduplicated |
| Forged signature / Google connection not configured | 401 / 503 |
| Unauthenticated or unlisted sender | inbox `ignored` (`sender_unauthenticated` / `sender_not_allowed`) |
| `ENABLE_LIVE_EMAIL=false`, Google not configured, recipient not allowed | outbox `blocked` before any dispatch row |
| Apps Script crashes after claiming | lease expires, outbox `unknown`, never resent |
| PDF digest mismatch in Apps Script | receipt `failed` (`gmail_transfer_corrupt`) |
| Nobody collects a reply for 24 hours | outbox `failed` (`mail_not_collected`) |
| Another trigger holds the script lock | `pollLumaMail`/`sendLumaMail` wait up to `LOCK_WAIT_MS` (25 s); on timeout the run throws (shows Failed). Before 2026-11-07 they used `tryLock(1000)` and returned silently, so a reply stayed `waiting` while the run showed Completed |

## Configuration (names only)

Backend: `EMAIL_ALLOWED_SENDERS`, `ENABLE_LIVE_EMAIL`, plus the existing `GOOGLE_COMPANY_ID`,
`GOOGLE_SHEET_ID` and `GOOGLE_CALLBACK_SECRET`. Apps Script Script Properties: the existing
`LUMA_*` values and optional `LUMA_GMAIL_LABEL` (default `LumaQuote`); it writes `LUMA_MAIL_CURSOR`,
`LUMA_LAST_MAIL_STATUS` and `LUMA_LAST_MAIL_SEND_STATUS`. `LUMA_MAIL_SELF_TEST_TO` (empty by default)
turns on a single-account test: the account's own mails count only when their To header contains
that address (the `+quotes` alias); the agent's replies go to the plain address and stay skipped.
`enableMailSelfTest` and `disableMailSelfTest` set and clear it; it was turned off after the live
test. See [configuration](CONFIGURATION.md).

## Tests and evidence

`tests/unit/test_email_ingress.py` (28 tests): address parsing, each authentication mechanism and
seven refusal cases, quoted-reply stripping in English and Arabic, reduction. `tests/integration/test_email.py`
(10 tests, real PostgreSQL and Storage, label `local-substitute`): stored once and deduplicated; forged
and unconfigured pushes; unauthenticated and unlisted senders; claim once, in-thread reply id, sent
receipt and replay; expired claim becomes `unknown`; failed receipt; live switch off; approved
quotation claim carries the exact staff PDF. Mutation checks: removing the authentication check or the
lease-expiry sweep made 3 tests fail.

Live (2026-11-07, user's Gmail, label `LumaQuote` with a filter on mail to the `+quotes` alias, sender
`mustafaalnagdy90@gmail.com` allowlisted, paid AI on): "i want 5 dl-001" was pushed within a minute,
Gmail authentication passed (`authenticated=true`), the model reply plus restatement was queued,
claimed and sent in the same thread about 90 seconds later. The sender's in-thread reply "yes" was
stripped of its quoted history to `yes`, made no model call and prepared quotation `LQ-F54A748B`
(5 x DL-001, 160.00) in review. One model call cost an estimated USD 0.000171. After staff approval
in the app (19:24:30) the quotation reply was queued, claimed and sent at 19:25:47; it arrived in
the same thread with the text "Quotation LQ-F54A748B, revision 1. Total USD 160.00 (tax excluded).
Staff-approved; valid until 14 Nov 2026" and one PDF attachment. **Not proven:** HTML-only mails,
the `getHeader` occurrence question, quotas, or behavior over days.

## Open gaps

Attachments (photos, voice) are not processed. HTML-only mails depend on Gmail's plain-text version.
The cursor is time-based; two mails with the same millisecond at a batch edge could be skipped.
No delivery or read state exists for email.
