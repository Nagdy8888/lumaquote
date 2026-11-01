"""Explicit paid canary for a synthetic label; no external calls in routine test runs."""

import json
import os
from pathlib import Path

import psycopg
import pytest
from luma.core.config import settings
from luma_agent.runtime.media import process_media
from test_manual_workflow import create_request, get_detail
from test_photo_intake import photo_job, upload_photo

pytestmark = pytest.mark.skipif(
    os.environ.get("LUMA_RUN_LIVE_PHOTO") != "1",
    reason="Paid synthetic vision canary requires explicit opt-in.",
)


def test_live_label_reading_remains_unconfirmed(environment, monkeypatch):
    """One reserved real vision call reads the generated label while leaving commercial selection/approval/send untouched."""
    env = environment
    cid = create_request(env)
    response = upload_photo(env, cid, Path("tests/fixtures/media/synthetic-label.png").read_bytes())
    assert response.status_code == 200
    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    settings.cache_clear()
    job = photo_job(env, cid)
    process_media(job, "image")
    current = get_detail(env, cid)
    message = next(m for m in current["messages"] if m["id"] == response.json()["message_id"])
    assert message["media_status"] == "ready" and message["image_available"]
    assert "DL-001" in message["body"] and "unconfirmed" in message["body"]
    assert current["quote"] is None and current["delivery"] == []
    with psycopg.connect(env["dsn"]) as conn:
        status, estimate = conn.execute(
            "select status,estimated from luma.usage where job_id=%s", (job["id"],)
        ).fetchone()
        assert status == "settled"
    Path(".local/live-photo-canary.json").write_text(
        json.dumps(
            {
                "model": "gpt-6-luna",
                "data": "Generated synthetic supplier label",
                "result": "Visible DL-001 read; fields unconfirmed; no approval/send",
                "estimated_usd": str(estimate),
                "actual_billing": "not retrieved",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
