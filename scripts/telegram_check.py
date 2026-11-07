"""Check the configured Telegram bot and list who has messaged it, to fill `TELEGRAM_ALLOWED_USERS`.

Usage: send any message to your bot from Telegram, stop the worker (it consumes updates), then
run `npm run telegram:check`. It calls `getMe` and a non-confirming `getUpdates` (no offset, no
wait), so pending updates stay queued for the worker. It prints the bot username and each
private sender's numeric user id and first name; it never prints the token or message text.
Exit code 1 when the token is missing or Telegram refuses it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "backend"))

from luma.features.messaging import telegram_client  # noqa: E402
from luma.features.messaging.errors import ProviderError  # noqa: E402


def main() -> int:
    """Print bot identity and pending private senders; return the process exit code."""
    try:
        bot = telegram_client.call("getMe")
        updates = telegram_client.get_updates(None, timeout=0)
    except ProviderError as error:
        print(f"Telegram check failed: {error.code}")
        return 1
    print(f"Bot: @{bot.get('username', '?')}")
    senders = {}
    for update in updates:
        message = update.get("message") if isinstance(update.get("message"), dict) else {}
        sender, chat = message.get("from") or {}, message.get("chat") or {}
        if chat.get("type") == "private" and isinstance(sender.get("id"), int):
            senders[sender["id"]] = str(sender.get("first_name", ""))[:40]
    if not senders:
        print("No pending private messages. Message the bot (and stop the worker), then run again.")
    for user_id, name in senders.items():
        print(f"User id {user_id}  ({name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
