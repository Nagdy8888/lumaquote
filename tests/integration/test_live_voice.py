"""Opt-in real transcription of local synthetic speech; never part of routine paid-free verification."""

import json
import os
from pathlib import Path

import psycopg
import pytest
from luma.core.config import settings
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail
from test_voice_intake import process_uploaded, upload

pytestmark = pytest.mark.skipif(
    os.environ.get("LUMA_RUN_LIVE_AUDIO") != "1",
    reason="Paid synthetic audio canary requires explicit opt-in.",
)


def test_real_synthetic_voice_is_readable_but_unconfirmed(environment, monkeypatch):
    """One reserved gpt-transcribe call links English transcript to private original without generating a quotation or send."""
    env = environment
    cid = create_request(env)
    data = Path(".local/synthetic-voice.wav").read_bytes()
    response = upload(env, cid, data)
    assert response.status_code == 200
    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    settings.cache_clear()
    process_uploaded(env, cid)
    current = get_detail(env, cid)
    message = next(m for m in current["messages"] if m["id"] == response.json()["message_id"])
    assert message["media_status"] == "ready"
    assert message["audio_available"]
    assert "downlight" in message["body"].lower()
    assert current["quote"] is None and current["delivery"] == []
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        usage = conn.execute(
            "select status,estimated from luma.usage where company_id=%s", (env["company"],)
        ).fetchone()
        assert usage["status"] == "settled"
    Path(".local/live-voice-canary.json").write_text(
        json.dumps(
            {
                "model": "gpt-transcribe",
                "source": "local System.Speech synthetic English supplier request",
                "provider_call": "verified",
                "transcript": "readable English product request; confirmation still required",
                "approval_or_send": False,
                "estimated_usd": str(usage["estimated"]),
                "actual_billing": "not retrieved",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
