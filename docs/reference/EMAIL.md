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
  -> pollLumaMail (every minute): labelled threads of the last 8 days, messages newer than the cursor, not from this account, max 5
  -> POST /callbacks/google/mail/inbound (signed) -> luma.inbox 'gm:<message id>' -> cursor moves
  -> inbox worker: Gmail authentication -> allowlist -> email conversation -> agent job
  -> agent reply or approved quotation -> outbox -> dispatcher: outbound.begin gates -> email_dispatch 'waiting'
  -> sendLumaMail (every minute): POST /claim -> reply in the customer's thread (PDF attached) -> POST /receipt
  -> outbox 'submitted' (or 'failed'), assistant message recorded
```

## How threads are found (fix of 2026-11-11)

The Gmail filter labels only mail sent to the `+quotes` alias, so only the customer's first mail
carries `LumaQuote`. A reply in the same thread addressed to the plain shop address (a YES
confirmation, "Accept, thanks", "Decline") has no label. `pendingMails_` therefore finds threads by
`label:LumaQuote newer_than:8d` and applies "newer than the cursor, not a draft, not our own message
(unless self-test)" per message in code. A thread whose newest message is not newer than the cursor
is skipped without reading its messages, and because Gmail returns threads newest-activity first the
scan stops at the first such thread (at most 4 pages of 50 threads per run). Mails are sorted oldest
first and cut to 5, so the cursor never passes an unsent older mail. Other senders inside a labelled
thread are still checked by the backend allowlist and authentication.

Why 8 days: a quotation is valid 7 days (D49), so an accept or decline can only matter inside that
window; the extra day absorbs timezone and clock slack. The window and the label are both tested by
Gmail against the same (labelled) message, so a thread stays visible for 8 days after its labelled
first mail; a reply after that is not collected.

The earlier query was `label:LumaQuote after:<cursor - 60 s>`. Gmail applies both terms to one
message, so once the cursor was more than 60 s past the labelled first mail the thread no longer
matched and plain-address replies were never collected. Found live on 2026-11-11: the stuck
"Accept, thanks" was collected within seconds after the thread label was re-applied by hand (which
labels every message in the thread). Re-verification after the fix is in Tests and evidence.

## Inputs and outputs

Push (`gmail_messages`, at most 5 mails from Apps Script, schema allows 10, body at most 256 KiB):
`message_id`, `thread_id` (Gmail hex ids), `from_header`, `reply_to`, `subject`, `date_ms`,
`auth_results` (Gmail's `Authentication-Results` header), `body` (plain text, Apps Script sends at
most 8000 characters), `attachments` (count). The stored event text is the new part of the body
(`strip_quoted` stops at an `On ... wrote:` line, an Arabic `في ... كتب ...:` line, `>` lines, an
`Original Message` divider, a `-- ` signature or a whole-line mobile client signature such as
"Sent from my iPhone", "Get Outlook for Android", "Sent from Mail for Windows" or "Sent from Yahoo
Mail"; a sentence that only mentions a phone is kept), else the subject, cut to 4000 characters. A mail
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

## Accepting or declining by reply (D49)

The quotation mail body (the caption built in `outbound.begin`, reused by `email_dispatch.queue`)
ends with "Reply ACCEPT to accept or DECLINE to decline." A customer replies in the same thread.
`email_ingress.reduce_mail` cuts the quoted history (`strip_quoted`), so the event text is only the
new text, for example `Accept`; the `Re: Quotation ...` subject is used only when the body is empty
and plays no part in the decision. `inbound.handle_message` sends the text through
`accept_customer_text`, where an exact phrase (`orders.acceptance.parse_answer`) is routed to
`orders.service.answer_quote` (see [INVENTORY](INVENTORY.md#customer-acceptance-and-orders-task-t3)).
The sender must already be authenticated and allowlisted. The confirmation notice is an ordinary
email reply queued through the same gated pull dispatch. "Accept, thanks" and an "Accept" above a
mobile signature are answers; a reply with a name or company signature line or a second sentence is
not an exact phrase and is treated as ordinary text (re-quote).

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
| Nobody collects a reply for 24 hours | outbox `failed` (`mail_not_collected`); a quotation reply also releases its stock reservation (`delivery_failed`, D49) |
| A quotation PDF over 5 MiB at claim time | dispatch and outbox `failed` (`pdf_too_large`), the mail is never offered, and the stock reservation is released (`delivery_failed`, D49) |
| A customer replies to the plain address after the labelled first mail is older than 8 days | not collected (outside the thread window); the quotation has expired by then |
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
seven refusal cases, quoted-reply stripping in English and Arabic, reduction. The Accept-by-reply path is
tested in `tests/integration/test_stock_acceptance.py` (`test_gmail_reply_with_quoted_history_accepts_the_quotation`). `tests/integration/test_email.py`
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

Apps Script lock contention (seen live 2026-11-11, not fixed): the Executions page showed many runs
failing after about 25-27 s while waiting for the shared script lock. Error rates over the shown
history: `sendLumaMail` 89%, `exportApprovedQuotations` 71%, `synchronizeSupplierWorkbook` 97%,
`pollLumaMail` 2%. All time-driven triggers fire each minute and share one lock, so they queue behind
each other and the sync (8-11 s) starves the others. A possible remedy is one one-minute trigger that
runs the tasks in sequence under one lock; it is not implemented and is a decision for the user (see
[morning actions](../MORNING_ACTIONS.md)).

Attachments (photos, voice) are not processed. HTML-only mails depend on Gmail's plain-text version.
The cursor is time-based; two mails with the same millisecond at a batch edge could be skipped.
No delivery or read state exists for email.
