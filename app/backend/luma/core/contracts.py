import hashlib
import json

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Reject undeclared input fields so callers cannot mass-assign privileged properties."""

    model_config = ConfigDict(extra="forbid")


class ResponseModel(BaseModel):
    """Shape an API response: declared fields are returned and undeclared database columns are dropped.

    Used for `response_model` so internal columns (company ids, actor ids) never reach the browser
    and the OpenAPI document states exactly what a client can rely on.
    """

    model_config = ConfigDict(extra="ignore")


def digest(value) -> str:
    """Return a stable SHA-256 identity for JSON-compatible business content; this is not encryption."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()
