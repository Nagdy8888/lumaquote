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
| `messaging/telegram_client.py` | Bot API calls: `getUpdates`, `sendMessage`, `sendDocument`, `getFile` plus the file download; maps failures to `ProviderError` |
| `messaging/telegram_ingress.py` | `reduce_update` (Update to event) and `poll_once` (fetch, persist, return the confirming offset) |
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

Accepted updates are `message` updates only (`allowed_updates=["message"]`). Edited messages are
not used. An update is kept only when the chat is `private`, the chat id equals the sender id,
the sender is not a bot, and `message_id` is positive. Event shapes:

| Telegram content | Event `type` | Notes |
| --- | --- | --- |
| `text` | `text` | first 4000 characters; `/start` (optionally `/start@bot`) queues the fixed greeting instead of starting agent work |
| `voice` or `audio` | `audio` | `file_id`; MIME from the message, `audio/ogg` if absent |
| `photo` | `image` | the largest size by width times height (the API promises no order); `image/jpeg` |
| anything else (sticker, document, location) | `unsupported` | the fixed "please send text, a voice note or a photo" notice |

Sends: text through `sendMessage` (`chat_id`, `text`, cut to 4096 characters). A quotation goes
through `sendDocument` as a multipart upload of the stored canonical PDF, with a caption cut to
1024 characters. The provider id stored on the outbox and message is `tg:<chat id>:<message id>`.

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
prints the request URL. `test_bot_token_never_reaches_logs` fails if that guard is removed
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

`tests/integration/test_telegram.py` (17 tests, real PostgreSQL and Storage, mock Bot API, label
`local-substitute`): private-chat reduction and photo choice; persist-before-confirm offsets;
allowlist; `/start` greeting; voice download into the media pipeline; two hostile-file cases; a
single send without a window; six failure classes; both gates; exact PDF bytes in `sendDocument`;
and the token kept out of logs. Live (2026-11-07): `getMe`, long polling, inbox processing and `sendMessage` worked with the real
bot. **Not proven:** `sendDocument` with a real PDF, real voice and photo file paths and MIME types, polling behavior over hours, or any delivery to a phone.

## Open gaps

The offset is not persisted, so a restart re-reads (and deduplicates) unconfirmed updates. Only
private chats are supported. Captions on photos and voice notes are ignored, as for WhatsApp. No
read state is shown for Telegram sends.
