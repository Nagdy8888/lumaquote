"""Actual private photo intake, offline normalization and durable failure behavior; no routine paid calls."""

import io
from uuid import uuid4

import psycopg
import pytest
from luma.core.config import settings
from luma_agent.runtime import media
from PIL import Image
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail


def photo_bytes():
    """Build a small explicitly synthetic PNG for actual content validation, without downloading outside images."""
    data = io.BytesIO()
    Image.new("RGB", (160, 100), "white").save(data, format="PNG")
    return data.getvalue()


def upload_photo(env, cid, data=None, key=None, version=None):
    """Submit only bytes and an optimistic version; no client field can choose storage paths or model outputs."""
    return env["api"].post(
        f"/api/conversations/{cid}/image",
        content=photo_bytes() if data is None else data,
        headers={
            **env["headers"],
            "Content-Type": "application/octet-stream",
            "Idempotency-Key": str(key or uuid4()),
            "Expected-Version": str(version or get_detail(env, cid)["conversation"]["version"]),
        },
    )


def photo_job(env, cid):
    """Lease only this fixture's own label-reading job, preserving other tenants and the original preparation queue."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        return conn.execute(
            """update luma.jobs set status='running',fence=fence+1,lease_until=now()+interval '120 seconds'
            where company_id=%s and conversation_id=%s and kind='read_photo' returning *""",
            (env["company"], cid),
        ).fetchone()


def test_photo_normalizes_to_private_jpeg_without_paid_reading(environment):
    """Only a decoded JPEG preview becomes available; photo bytes cannot be served as audio or grant a quotation."""
    env = environment
    cid = create_request(env)
    uploaded = upload_photo(env, cid)
    assert uploaded.status_code == 200
    mid = uploaded.json()["message_id"]
    media.process_media(photo_job(env, cid), "image")
    message = next(m for m in get_detail(env, cid)["messages"] if m["id"] == mid)
    assert message["image_available"] and not message["audio_available"]
    assert message["media_status"] == "needs_staff"
    preview = env["api"].get(f"/api/media/{mid}/image", headers=env["headers"])
    assert preview.status_code == 200 and preview.content[:2] == b"\xff\xd8"
    assert env["api"].get(f"/api/media/{mid}/audio", headers=env["headers"]).status_code == 404
    assert get_detail(env, cid)["quote"] is None


def test_corrupt_photo_is_rejected_before_provider_use(environment):
    """Claimed image bytes cannot bypass actual restricted decoding."""
    env = environment
    cid = create_request(env)
    response = upload_photo(env, cid, b"not an image")
    assert response.status_code == 200
    media.process_media(photo_job(env, cid), "image")
    assert get_detail(env, cid)["messages"][-1]["media_status"] == "rejected"
    assert (
        env["api"]
        .get(f"/api/media/{response.json()['message_id']}/image", headers=env["headers"])
        .status_code
        == 404
    )


def test_photo_stream_limit_and_replay_binding(environment):
    """Same bytes/precondition replay once; new bytes under an old identity and bodies above 5 MB are denied."""
    env = environment
    cid = create_request(env)
    version = get_detail(env, cid)["conversation"]["version"]
    key = uuid4()
    first = upload_photo(env, cid, key=key, version=version)
    assert first.status_code == 200
    assert upload_photo(env, cid, key=key, version=version).json() == first.json()
    assert upload_photo(env, cid, b"changed", key, version).status_code == 409
    assert upload_photo(env, cid, b"x" * (5 * 1024 * 1024 + 1)).status_code == 413


def test_unknown_provider_outcome_retains_reservation_and_never_retries(environment, monkeypatch):
    """A simulated accepted-but-lost provider response is conservative across actual database/storage/job boundaries."""
    env = environment
    cid = create_request(env)
    uploaded = upload_photo(env, cid)
    assert uploaded.status_code == 200
    monkeypatch.setenv("ENABLE_PAID_AI", "true")
    settings.cache_clear()
    calls = []

    def timeout(*args):
        """Simulate only the external response loss; parsing, authorization, reservation and persistence remain real."""
        calls.append(True)
        raise TimeoutError("Synthetic lost provider response")

    monkeypatch.setattr(media, "read_media", timeout)
    job = photo_job(env, cid)
    with pytest.raises(TimeoutError):
        media.process_media(job, "image")
    assert get_detail(env, cid)["messages"][-1]["media_status"] == "unknown"
    media.process_media(job, "image")
    assert calls == [True]
    with psycopg.connect(env["dsn"]) as conn:
        assert (
            conn.execute("select status from luma.usage where job_id=%s", (job["id"],)).fetchone()[0]
            == "unknown"
        )
