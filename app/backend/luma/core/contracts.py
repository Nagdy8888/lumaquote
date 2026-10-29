import hashlib
import json

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Reject undeclared input fields so callers cannot mass-assign privileged properties."""

    model_config = ConfigDict(extra="forbid")


def digest(value) -> str:
    """Return a stable SHA-256 identity for JSON-compatible business content; this is not encryption."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()
