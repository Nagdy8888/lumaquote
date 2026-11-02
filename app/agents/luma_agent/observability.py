"""Detailed, masked LangSmith tracing for worker jobs (decision D24, rule R13).

What is exported when `LANGSMITH_TRACING=true` and a LangSmith key is configured:

- one root run per worker job (`luma.job.<kind>`), whose inputs are the job identity and
  whose outputs are the outcome (`done`, `blocked`, `failed`) and error class;
- every LangGraph step nested under it (LangChain's tracer reads the client and parent from
  the LangSmith tracing context set here, so graph runs use the same masking client);
- one `llm` child run per OpenAI call (Responses extraction, label reading, transcription,
  embeddings) with the model, instructions, input text and parsed output, recorded through
  `model_call()` by the adapters.

Masking runs on every exported payload (inputs, outputs, metadata) through the client's
`hide_inputs` / `hide_outputs` / `hide_metadata` hooks, so a caller cannot forget it:

- configured secret values (every `SecretStr` setting) are replaced by `[secret]`;
- API keys, bearer tokens, JWTs, HMAC signatures and `token=`/`signature=`-style URL
  parameters are replaced by `[secret]`;
- phone numbers (`+` international form, 10-15 consecutive digits such as WhatsApp ids, and
  common local forms starting with 0) are replaced by `[phone]`;
- base64 `data:` URLs and raw `bytes` are replaced by a size note, so audio and image content
  never leaves the machine.

Message text, transcripts, label readings, retrieval results and quotation content are kept
(the owner wants to inspect behavior). Masking is pattern-based: a phone number written in
an unusual form (for example spelled out in words) is not detected. Tracing failures never
fail a job: export problems are logged by class name only.
"""

import logging
import re
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from langsmith import Client, get_tracing_context, trace, tracing_context
from luma.core.config import settings
from pydantic import SecretStr

logger = logging.getLogger("luma.tracing")

SECRET = "[secret]"
PHONE = "[phone]"
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\blsv2_[A-Za-z0-9_]{16,}"),
    re.compile(r"\bEAA[A-Za-z0-9]{20,}"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"\beyJ[\w\-]{8,}\.[\w\-]{8,}\.[\w\-]{8,}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/\-]{12,}=*"),
    re.compile(r"(?i)\bsha256=[0-9a-f]{64}\b"),
    re.compile(r"(?i)\b(token|signature|sig|secret|api_?key|apikey|password|access_token)=[^&\s\"']+"),
]
PHONE_PATTERNS = [
    re.compile(r"\+\d[\d \-().]{7,18}\d"),
    re.compile(r"(?<![\w-])\d{10,15}(?![\w-])"),
    re.compile(r"(?<![\w-])0\d{2,4}[ \-]\d{3}[ \-]\d{3,4}(?![\w-])"),
]
DATA_URL = re.compile(r"data:[\w/+.\-]+;base64,[A-Za-z0-9+/=]+")


@lru_cache(maxsize=1)
def configured_secrets() -> tuple[str, ...]:
    """Return the literal values of every configured `SecretStr` setting (8+ characters), longest first.

    Literal replacement catches credentials whose format no pattern knows (database URLs,
    webhook secrets). Cached per process; `reset()` clears it when settings change in tests.
    """
    config = settings()
    values = []
    for name in type(config).model_fields:
        value = getattr(config, name)
        if isinstance(value, SecretStr) and len(value.get_secret_value()) >= 8:
            values.append(value.get_secret_value())
    return tuple(sorted(set(values), key=len, reverse=True))


def mask_text(text: str) -> str:
    """Mask secrets, phone numbers and inline media in one string; other text is unchanged."""
    for value in configured_secrets():
        text = text.replace(value, SECRET)
    text = DATA_URL.sub(lambda match: f"[media omitted: {len(match.group(0))} chars]", text)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(SECRET, text)
    for pattern in PHONE_PATTERNS:
        text = pattern.sub(PHONE, text)
    return text


def mask(value: Any, depth: int = 0) -> Any:
    """Return a masked copy of a trace payload (dicts, lists, tuples, strings, bytes, scalars).

    Bytes become a size note; nesting deeper than 40 levels is cut to protect the exporter.
    Keys are masked too, because providers sometimes echo values as keys.
    """
    if depth > 40:
        return "[depth limit]"
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"[{len(bytes(value))} bytes omitted]"
    if isinstance(value, dict):
        return {mask_text(str(key)): mask(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [mask(item, depth + 1) for item in value]
    return value


def tracing_enabled() -> bool:
    """True when the operator enabled LangSmith tracing and configured a key."""
    config = settings()
    return bool(config.langsmith_tracing and config.langsmith_api_key.get_secret_value())


@lru_cache(maxsize=1)
def masked_client() -> Client:
    """Build the one LangSmith client used for every exported run, with masking on all payloads."""
    config = settings()
    return Client(
        api_key=config.langsmith_api_key.get_secret_value(),
        api_url=config.langsmith_endpoint,
        hide_inputs=mask,
        hide_outputs=mask,
        hide_metadata=mask,
    )


def reset() -> None:
    """Forget cached secrets and client (tests call this after changing settings)."""
    configured_secrets.cache_clear()
    masked_client.cache_clear()


@contextmanager
def job_trace(job: dict) -> Iterator[Any]:
    """Run one worker job inside a masked root trace, or with tracing explicitly off.

    Yields the root run (or None when tracing is off). The caller records the outcome with
    `finish(run, outcome, error)`. All nested LangGraph and model-call runs attach to this
    root through the tracing context. When tracing is disabled the context is still set to
    `enabled=False`, so environment variables cannot switch on unmasked automatic tracing.
    """
    if not tracing_enabled():
        with tracing_context(enabled=False):
            yield None
        return
    config = settings()
    client = masked_client()
    identity = {
        "job_id": str(job["id"]),
        "job_kind": job.get("kind"),
        "company_id": str(job.get("company_id")),
        "conversation_id": str(job.get("conversation_id")),
    }
    with (
        tracing_context(enabled=True, client=client, project_name=config.langsmith_project),
        trace(
            f"luma.job.{job.get('kind')}",
            "chain",
            inputs={**identity, "payload": job.get("payload") or {}},
            project_name=config.langsmith_project,
            client=client,
            tags=["luma", f"job:{job.get('kind')}"],
            metadata=identity,
        ) as run,
    ):
        yield run


def finish(run: Any, outcome: str, error: str | None = None) -> None:
    """Record the job outcome on its root run and flush the export; never raises."""
    if run is None:
        return
    try:
        run.end(outputs={"outcome": outcome, "error": error})
    except Exception as failure:
        logger.warning("Trace finish failed: %s", type(failure).__name__)


def flush() -> None:
    """Send buffered runs to LangSmith; export problems are logged by class name only."""
    if not tracing_enabled():
        return
    try:
        masked_client().flush()
    except Exception as failure:
        logger.warning("Trace export unavailable: %s", type(failure).__name__)


@contextmanager
def masked_or_off() -> Iterator[None]:
    """Keep an active masked job trace, otherwise force tracing off for the enclosed work.

    Graph runtimes and provider adapters are also called outside the worker (tests, the
    evaluation harness, scripts). Without this guard an environment variable such as
    `LANGSMITH_TRACING=true` could make LangChain export unmasked payloads through its
    default client. Inside `job_trace` the context already carries `masked_client()`.
    """
    context = get_tracing_context()
    parent = context.get("parent")
    client = context.get("client") or (parent.client if parent is not None else None)
    if context.get("enabled") and tracing_enabled() and client is masked_client():
        yield
        return
    with tracing_context(enabled=False):
        yield


@contextmanager
def model_call(name: str, model: str, inputs: dict) -> Iterator[Any]:
    """Record one provider call as an `llm` child run of the current job trace.

    `inputs` should hold the model-facing content (instructions, input text, file
    description). Callers set outputs with `run.end(outputs=...)` or `set_outputs(run, ...)`.
    Outside an enabled job trace this yields None and records nothing.
    """
    if not tracing_enabled():
        yield None
        return
    with trace(name, "llm", inputs={"model": model, **inputs}, metadata={"ls_model_name": model}) as run:
        yield run


def set_outputs(run: Any, outputs: dict) -> None:
    """Attach outputs to a model-call run when tracing is active; a no-op otherwise."""
    if run is not None:
        run.end(outputs=outputs)
