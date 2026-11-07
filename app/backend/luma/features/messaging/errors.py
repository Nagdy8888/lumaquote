"""Provider-neutral classification of WhatsApp transport failures.

Both adapters (Meta Graph in `whatsapp_client`, Twilio in `twilio_client`) raise only this
type, so callers decide retry behavior from `kind` without knowing which provider ran:

- `rejected`: the provider gave a definite refusal; nothing was delivered.
- `unreachable`: the connection could not be made, so the request was not sent.
- `unknown`: a timeout, dropped connection or 5xx after the request left; the message may
  or may not have been accepted and must be reconciled from provider receipts, never resent.
"""

import re

CODE = re.compile(r"[^0-9a-z_]")


class ProviderError(Exception):
    """A classified provider failure carrying only a short opaque code, never provider payloads."""

    def __init__(self, kind: str, code: str):
        """Record the classification (`rejected`, `unreachable` or `unknown`) and a bounded code."""
        super().__init__(kind)
        self.kind, self.code = kind, CODE.sub("", code.lower())[:40] or "error"
