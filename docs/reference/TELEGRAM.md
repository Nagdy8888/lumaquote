# Telegram channel (Bot API, long polling)

This explains the Telegram bot channel added in decision D44: what it trusts, how a message
moves through it, what it writes, and what it does and does not prove. It is verified against a
mock Bot API transport in `tests/integration/test_telegram.py`, plus one `live` smoke test on
2026-11-07: real bot, one allowlisted user, two inbound texts stored and processed, two text replies
accepted by Telegram. A live quotation PDF has not been sent yet. Live steps are in [morning actions](../MORNING_ACTIONS.md). Live sending
is off by default (`ENABLE_LIVE_TELEGRAM=false`).

## Why Telegram

WhatsApp test access was blocked twice. Meta refuses app creation for the user's restricted
business portfolio (2026-11-07), and Twilio's WhatsApp Sandbox is not free for the user in Egypt.
The Telegram Bot API costs nothing, needs only a token from @BotFather, and with long polling
needs no public URL, tunnel or webhook. WhatsApp code (Meta and Twilio) stays in place unchanged.

## Actors and authority

| Actor | Can | Cannot |
| --- | --- | --- |
| Telegram (Bot API over TLS) | deliver updates the worker asks for; accept sends | choose the company, approve, price or bypass the allowlist |
| Customer (allowlisted user id, private chat) | open or extend a conversation; send text, voice, audio, photos | reach the agent from a group, as a bot, or when not on `TELEGRAM_ALLOWED_USERS` |
| Worker | poll, store, process, send after `outbound.begin` passes | send without the live switch, token and allowlisted recipient |
| Staff | approve quotations, take over, reply (same rules as WhatsApp) | — |

The bot token is the only credential. It authenticates calls the worker makes. There is no
inbound HTTP endpoint, so there is no webhook signature to forge. The company is
`TELEGRAM_COMPANY_ID` from configuration; nothing in an update selects a tenant.

## Modules and call flow

| Module | Role |
| --- | --- |
| `messaging/telegram_client.py` | Bot API calls: `getUpdates`, `sendMessage`, `sendDocument` (with optional inline buttons), `answerCallbackQuery`, `editMessageReplyMarkup` (clears the buttons), `getFile` plus the file download; maps failures to `ProviderError` |
| `messaging/telegram_ingress.py` | `reduce_update` and `reduce_callback` (Update to event) and `poll_once` (fetch, persist, return the confirming offset) |
| `luma_agent/worker.py` | starts the `poll_telegram` daemon thread when a token and company are configured |
| `messaging/inbound.py` | same inbox processing as WhatsApp, with `channel` picking the allowlist and conversation channel |
| `messaging/outbound.py`, `provider.py` | same three-phase send, with the adapter picked by the conversation channel |
| `scripts/telegram_check.py` (`npm run telegram:check`) | prints the bot username and pending private sender ids for setup |

```
Customer -> Telegram -> getUpdates (worker thread, 25 s long poll)
  -> reduce_update -> persist to luma.inbox (key tg:<chat>:<message>)
  -> next getUpdates with offset = max update_id + 1 (this confirms the batch)
  -> inbox worker: allowlist -> open/extend conversation (channel 'telegram')
  -> same agent graph, approval and outbox as every channel
  -> dispatcher -> outbound.begin (live switch, token, allowlist) -> sendMessage / sendDocument
```

## Inputs and outputs

Accepted updates are `message` and `callback_query` updates (`allowed_updates=["message",
"callback_query"]`, D49). Edited messages are not used. An update is kept only when the chat is `private`, the chat id equals the sender id,
the sender is not a bot, and `message_id` is positive. Event shapes:

| Telegram content | Event `type` | Notes |
| --- | --- | --- |
| `text` | `text` | first 4000 characters; `/start` (optionally `/start@bot`) queues the fixed greeting instead of starting agent work |
| `voice` or `audio` | `audio` | `file_id`; MIME from the message, `audio/ogg` if absent |
| `photo` | `image` | the largest size by width times height (the API promises no order); `image/jpeg` |
| anything else (sticker, document, location) | `unsupported` | the fixed "please send text, a voice note or a photo" notice |
| `callback_query` from an Accept or Decline button | `quote_answer` | see [Quotation buttons](#quotation-buttons-accept-and-decline-d49) |

Sends: text through `sendMessage` (`chat_id`, `text`, cut to 4096 characters). A quotation goes
through `sendDocument` as a multipart upload of the stored canonical PDF, with a caption cut to
1024 characters. The provider id stored on the outbox and message is `tg:<chat id>:<message id>`.

## Quotation buttons: Accept and Decline (D49)

Fields checked against the Bot API page on 2026-11-08 (R3): `sendDocument.reply_markup` takes an
`InlineKeyboardMarkup`; with a multipart upload it must be a JSON-serialized string field.
`InlineKeyboardButton.callback_data` is 1-64 bytes. A `CallbackQuery` carries `id`, `from`,
optional `message` (a `Message`, or an `InaccessibleMessage` with only `chat`, `message_id`, `date`
once the message is old) and `data`. `answerCallbackQuery` takes `callback_query_id` and an
optional `text` of 0-200 characters; Telegram shows a progress bar on the button until it is called.
`getUpdates.allowed_updates` is a JSON list of update types. `editMessageReplyMarkup` (read 2026-11-11)
takes `chat_id` (Integer or String, required without `inline_message_id`), `message_id` (Integer,
same rule) and an optional `reply_markup` (`InlineKeyboardMarkup`); omitting `reply_markup`
removes the inline keyboard, and a bot's own message is answered with the edited `Message`.

- **Send.** A quotation `sendDocument` to a Telegram conversation (`outbound.answer_buttons`) carries
  `reply_markup={"inline_keyboard":[[{"text":"Accept","callback_data":"acc:<quote id>"},
  {"text":"Decline","callback_data":"dec:<quote id>"}]]}` (40 bytes each). The caption also ends
  with "Reply ACCEPT to accept or DECLINE to decline." so a typed answer works too. Text replies,
  and the other adapters (which ignore an optional `buttons` argument), get no keyboard.
- **Ingress.** `reduce_callback` keeps a press only when the button sits on a message in a
  `private` chat, `from.id` equals `chat.id`, the presser is not a bot, the query id matches
  `[A-Za-z0-9_-]{1,64}` and `data` is exactly `acc:<uuid>` or `dec:<uuid>`. The event is
  `{id: "tgcb:<callback id>", from, name, provider, channel: "telegram", type: "quote_answer",
  answer, quote_id, callback_id, message_id}` (`message_id` is the id of the message the button
  sits on, kept only when it is a positive integer) and is stored in `luma.inbox` under that id (dedupe on
  redelivery). Anything else is skipped but still confirmed by the offset.
- **Processing.** `inbound.handle_message` applies the normal sender allowlist, opens the sender's
  own conversation and calls `participation.accept_quote_button`: rate limit (6 per minute,
  shared with typed text), store the customer message "[Button] Accept" or "[Button] Decline"
  under the event id, then `orders.service.answer_quote(via='telegram_button', quote_id=...)`. The
  `quote_id` is only a claim. It must equal the newest quotation of the sender's own
  conversation and that quotation must be answerable (see [INVENTORY](INVENTORY.md#customer-acceptance-and-orders-task-t3)),
  so another chat's id or an old button changes nothing: it raises an `acceptance_refused` alert
  and the customer gets the fixed refusal notice.
- **Acknowledge.** After the inbox row is settled and committed, `inbound.acknowledge_button`
  calls `answerCallbackQuery` with the fixed text "Recorded" (no text when the press was ignored
  or failed). The call is outside any database transaction, best effort and never retried. A
  failure logs only `Telegram callback answer failed: <opaque code>`: no callback id, token,
  URL or customer text. A requeued (rate-limited) press is acknowledged when it finally settles; a
  press that is never acknowledged only leaves the spinner running until Telegram times it out.
- **Clear the buttons.** When the press was processed (inbox row `done`: the answer was recorded,
  or an old or forged button was refused and the customer got the refusal notice),
  `inbound.acknowledge_button` then calls `telegram_client.clear_buttons(chat id, message id)`, which
  sends `editMessageReplyMarkup` with `chat_id` (the presser's id, equal to the chat id) and
  `message_id` and no `reply_markup`, so the Accept and Decline buttons disappear from that
  quotation message and cannot be pressed twice. The same rules apply as for the acknowledgement:
  after the commit, no database transaction, never retried, and a failure (for example the message
  is too old, was deleted, or the keyboard is already gone: "message is not modified") logs only
  `Telegram button removal failed: <opaque code>`. A press from a sender off the allowlist
  (`ignored`) and a press that failed or is requeued leave the message untouched. A press whose
  update carries no message id leaves its keyboard, and a later press on it is answered by the
  binding rules above.

## State transitions

Inbox rows follow the WhatsApp rules (`queued`, `processing`, `done`, `ignored`, `failed`, five
attempts). Outbox rows: `queued`, `submitting`, then `submitted`, `failed` or `unknown`, or
`blocked` before any call. The Bot API has no delivery or read receipts, so a Telegram send never
moves past `submitted`. There is no 24-hour service window for Telegram. A bot can only message
users who started it, and the allowlist narrows that further.

## Database writes and transactions

Migration `20261107010000_telegram_channel.sql` widens `conversations_channel_check` to
`('local_test', 'whatsapp', 'telegram')`. No new table. `persist` writes one inbox row per message
in one transaction before the offset is advanced. Conversation creation takes the advisory lock
`telegram:<company>:<user id>`. Outbox and message writes are the shared ones in `outbound.record`.

## Idempotency

Inbox key `tg:<chat id>:<message id>` (message ids are unique per chat). A batch that is stored
but not yet confirmed is resent by Telegram after a crash and deduplicated by that key. The offset
lives in memory. After a restart the first poll omits it and receives every unconfirmed update,
which Telegram keeps for up to 24 hours. Sends have no provider idempotency key. The `submitting`
marker plus never retrying `unknown` prevent duplicates.

## Limits and cost

From the Bot API page (version 10.3, read 2026-11-07; re-check before relying on them): free to
use; about 30 messages per second per bot; text up to 4096 characters, captions up to 1024;
uploads up to 50 MB, downloads up to 20 MB; file links valid at least one hour. Media limits in
this app are tighter: 10 MB audio, 5 MB images.

## External effects and secrets

Every Bot API URL contains the token (`/bot<token>/...`). The client never logs URLs, converts
exceptions to codes `from None`, and holds the `httpx` logger at WARNING because its INFO line
prints the request URL. The worker also holds `httpx2` at WARNING: the OpenAI SDK 3.x sends through that
package, which logs its own request lines. `test_bot_token_never_reaches_logs` fails if that guard is removed
(mutation-checked). `telegram:check` prints user ids and first names, never tokens or message text.

## Failures and recovery

| Condition | Result |
| --- | --- |
| Telegram unreachable or refusing `getUpdates` | offset unchanged, warning with an opaque code, next poll retries |
| Inbox storage down during a poll | exception class logged, offset unchanged, 5 s pause |
| Group chat, bot sender, mismatched chat id | skipped, never stored |
| Sender not on `TELEGRAM_ALLOWED_USERS` | inbox row `ignored` |
| Declared file over the limit, bad file path, denied type | attachment refused with the fixed notice, no download |
| 403 (user blocked the bot), 429 (flood), other 4xx, connect error | outbox `failed`, `telegram_<code>` or `connect_error` |
| Timeout, 5xx, success without `message_id` | outbox `unknown`, never resent |
| Live switch off, token missing, recipient not allowed | outbox `blocked` |
| A webhook is set on the bot | `getUpdates` refused, so polling fails until the webhook is deleted (not done automatically) |

## Configuration (names only)

`TELEGRAM_BOT_TOKEN` (secret), `TELEGRAM_COMPANY_ID`, `TELEGRAM_ALLOWED_USERS` (comma-separated
numeric user ids; empty admits nobody), `ENABLE_LIVE_TELEGRAM`. See [configuration](CONFIGURATION.md).

## Tests and evidence

`tests/integration/test_stock_acceptance.py` adds the button tests (callback reduction table,
buttons in `sendDocument`, accept and decline presses, redelivery, forged and old quote ids, a
presser off the allowlist, a failing `answerCallbackQuery`, the keyboard cleared after accept, decline
and a refused button but not for an ignored presser, and a failing `editMessageReplyMarkup`). `tests/integration/test_telegram.py` (17 tests, real PostgreSQL and Storage, mock Bot API, label
`local-substitute`): private-chat reduction and photo choice; persist-before-confirm offsets;
allowlist; `/start` greeting; voice download into the media pipeline; two hostile-file cases; a
single send without a window; six failure classes; both gates; exact PDF bytes in `sendDocument`;
and the token kept out of logs. Live (2026-11-07): `getMe`, long polling, inbox processing and `sendMessage` worked with the real
bot. **Not proven:** `sendDocument` with a real PDF, real voice and photo file paths and MIME types, polling behavior over hours, or any delivery to a phone.

## Open gaps

The Accept and Decline buttons are proven only against the mock Bot API; a live press needs the
running bot (see [morning actions](../MORNING_ACTIONS.md)), including the keyboard removal. If
Telegram refuses the removal the keyboard stays, and a later press is answered by the binding rules above.
The offset is not persisted, so a restart re-reads (and deduplicates) unconfirmed updates. Only
private chats are supported. Captions on photos and voice notes are ignored, as for WhatsApp. No
read state is shown for Telegram sends.
