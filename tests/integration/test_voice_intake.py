"""Actual Auth, private Storage, database and restricted audio sandbox; no paid calls by default."""

import io
import wave
from uuid import uuid4

import psycopg
import pytest
from luma.features.conversations.service import add_message
from luma_agent.runtime.audio import process_audio
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail, make_draft, post


def wav_bytes():
    """Generate one second of explicitly synthetic silence to exercise actual decoding without private speech."""
    data = io.BytesIO()
    with wave.open(data, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0\0" * 16000)
    return data.getvalue()


def upload(env, cid, data, key=None, version=None):
    """Submit actual binary bytes with the canonical conversation precondition and opaque operation identity."""
    version = version or get_detail(env, cid)["conversation"]["version"]
    return env["api"].post(
        f"/api/conversations/{cid}/audio",
        content=data,
        headers={
            **env["headers"],
            "Idempotency-Key": str(key or uuid4()),
            "Expected-Version": str(version),
            "Content-Type": "application/octet-stream",
        },
    )


def process_uploaded(env, cid):
    """Lease only this fixture's transcription job; existing preparation jobs are not run by this helper."""
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        job = conn.execute(
            """update luma.jobs set status='running',fence=1,lease_until=now()+interval '120 seconds'
            where company_id=%s and conversation_id=%s and kind='transcribe' returning *""",
            (env["company"], cid),
        ).fetchone()
    process_audio(job)


def test_private_audio_decodes_but_paid_ai_stays_disabled(environment):
    """An authorized voice note becomes playable normalized audio, with honest manual state and no inference reservation."""
    env = environment
    cid = create_request(env)
    response = upload(env, cid, wav_bytes())
    assert response.status_code == 200
    mid = response.json()["message_id"]
    process_uploaded(env, cid)
    current = get_detail(env, cid)
    assert "transcription is disabled" in current["messages"][-1]["body"]
    audio = env["api"].get(f"/api/media/{mid}/audio", headers=env["headers"])
    assert audio.status_code == 200 and audio.content[:4] == b"RIFF"
    assert get_detail(env, cid)["quote"] is None
    with psycopg.connect(env["dsn"]) as conn:
        assert (
            conn.execute("select count(*) from luma.usage where company_id=%s", (env["company"],)).fetchone()[
                0
            ]
            == 0
        )


def test_corrupt_voice_note_fails_safely(environment):
    """File names and claimed MIME cannot cause arbitrary bytes to reach transcription."""
    env = environment
    cid = create_request(env)
    response = upload(env, cid, b"not an audio recording")
    assert response.status_code == 200
    process_uploaded(env, cid)
    assert "could not be safely processed" in get_detail(env, cid)["messages"][-1]["body"]
    assert (
        env["api"]
        .get(f"/api/media/{response.json()['message_id']}/audio", headers=env["headers"])
        .status_code
        == 404
    )


def test_binary_replay_is_bound_to_exact_bytes(environment):
    """Retries replay the original message without duplicate media/jobs; changed bytes conflict under the same key."""
    env = environment
    cid = create_request(env)
    key = uuid4()
    version = get_detail(env, cid)["conversation"]["version"]
    first = upload(env, cid, wav_bytes(), key, version)
    assert first.status_code == 200
    assert upload(env, cid, wav_bytes(), key, version).json() == first.json()
    assert upload(env, cid, b"different", key, version).status_code == 409
    with psycopg.connect(env["dsn"]) as conn:
        assert (
            conn.execute("select count(*) from luma.media where company_id=%s", (env["company"],)).fetchone()[
                0
            ]
            == 1
        )


def test_new_voice_note_invalidates_approved_offer(environment):
    """Unprocessed customer audio is already a request change and blocks the previously approved dispatch."""
    env = environment
    cid = create_request(env)
    make_draft(env, cid)
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 200
    )
    assert upload(env, cid, wav_bytes()).status_code == 200
    current = get_detail(env, cid)
    assert current["quote"]["status"] == "superseded"
    assert current["delivery"][0]["status"] == "blocked"


def test_audio_access_is_scoped_and_size_bounded(environment):
    """Unknown media identities are hidden and an oversized actual body is rejected before storage."""
    env = environment
    cid = create_request(env)
    assert env["api"].get(f"/api/media/{uuid4()}/audio", headers=env["headers"]).status_code == 404
    assert upload(env, cid, b"x" * (10 * 1024 * 1024 + 1)).status_code == 413


def test_media_cannot_relabel_another_conversations_message(environment):
    """The database itself rejects mismatched message/conversation provenance, including privileged inserts."""
    env = environment
    first, second = create_request(env), create_request(env)
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        message = add_message(conn, env["company"], first, "customer", "Synthetic audio", kind="audio")
        with pytest.raises(psycopg.errors.ForeignKeyViolation) as failure:
            conn.execute(
                "insert into luma.media(message_id,company_id,conversation_id,original_path) values(%s,%s,%s,%s)",
                (message, env["company"], second, f"{env['company']}/media/invalid-fixture"),
            )
        assert failure.value.diag.constraint_name == "media_message_conversation_fk"
        conn.rollback()
