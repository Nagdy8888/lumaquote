"""Trace payloads are allowlisted even when worker input contains private business fields."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from luma_agent import observability
from pydantic import SecretStr


@pytest.mark.parametrize("fails", [False, True])
def test_trace_exports_only_opaque_identity_and_safe_outcome(monkeypatch, fails):
    """No customer text, recipient, credentials, or arbitrary job metadata is forwarded; failed clients also close."""
    sent = []
    closed = []

    class CapturingClient:
        """Capture the exact outbound SDK contract without creating any external trace."""

        def __init__(self, **options):
            """Require synchronous export so acceptance is observable by the worker."""
            assert options["auto_batch_tracing"] is False

        def create_run(self, **payload):
            """Record the allowlisted trace and optionally emulate an unavailable service."""
            sent.append(payload)
            if fails:
                raise RuntimeError("Trace service unavailable")

        def close(self):
            """Observe that resources close on both acceptance and provider rejection."""
            closed.append(True)

    config = SimpleNamespace(
        langsmith_tracing=True,
        langsmith_api_key=SecretStr("unit-test-only"),
        langsmith_endpoint="https://example.invalid",
        langsmith_project="synthetic-test",
    )
    monkeypatch.setattr(observability, "settings", lambda: config)
    monkeypatch.setattr(observability, "Client", CapturingClient)
    identity = uuid4()
    job = {"id": identity, "recipient": "private", "payload": {"text": "private text", "secret": "private"}}
    if fails:
        with pytest.raises(RuntimeError):
            observability.trace_outcome(job, "done")
    else:
        assert observability.trace_outcome(job, "done")
    assert sent[0]["inputs"] == {"job_id": str(identity)}
    assert sent[0]["outputs"] == {"status": "done"}
    assert "private" not in str(sent)
    assert closed == [True]
