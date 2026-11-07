"""Dependency outages fail closed with a safe retryable 503, leave no half-written state and recover.

The database and Storage are made unreachable by pointing the application at a closed local port or by
making the Storage client raise a transport error; nothing external is contacted. Synthetic data only.
"""

import httpx
import psycopg
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.features.media import intake
from luma.main import app
from psycopg.rows import dict_row
from test_manual_workflow import create_request, get_detail
from test_voice_intake import upload, wav_bytes

DEAD_DSN = "postgresql://luma_api:secret-outage-password@127.0.0.1:9/postgres"


def test_database_outage_is_a_safe_retryable_503(environment, monkeypatch):
    """With PostgreSQL unreachable the API answers 503 with retry guidance and no connection details, then recovers."""
    env = environment
    cid = create_request(env)
    monkeypatch.setenv("LUMA_API_DATABASE_URL", DEAD_DSN)
    settings.cache_clear()
    with TestClient(app, raise_server_exceptions=False) as client:
        for response in (
            client.get("/api/workspace", headers=env["headers"]),
            client.get(f"/api/conversations/{cid}", headers=env["headers"]),
        ):
            assert response.status_code == 503 and response.headers["retry-after"] == "30"
            assert "secret-outage-password" not in response.text and "127.0.0.1" not in response.text
    monkeypatch.undo()
    settings.cache_clear()
    assert get_detail(env, cid)["conversation"]["id"] == cid


def test_storage_outage_leaves_nothing_half_written_and_recovers(environment, monkeypatch):
    """A Storage transport failure during a voice upload is a 503, creates no message, media row or job, and a retry works."""
    env = environment
    cid = create_request(env)

    def counts():
        """Count the rows an accepted upload would have created for this conversation."""
        with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
            return conn.execute(
                """select (select count(*) from luma.messages where conversation_id=%(c)s) messages,
                (select count(*) from luma.media where conversation_id=%(c)s) media,
                (select count(*) from luma.jobs where conversation_id=%(c)s and kind='transcribe') jobs""",
                {"c": cid},
            ).fetchone()

    before = counts()
    original = intake.put_file

    def down(*args, **kwargs):
        """Fail the way an unreachable Storage service does."""
        raise httpx.ConnectError("Storage unreachable")

    monkeypatch.setattr(intake, "put_file", down)
    with TestClient(app, raise_server_exceptions=False) as client:
        env_down = {**env, "api": client}
        failed = upload(env_down, cid, wav_bytes())
    assert failed.status_code == 503 and failed.headers["retry-after"] == "30"
    assert counts() == before
    monkeypatch.setattr(intake, "put_file", original)
    assert upload(env, cid, wav_bytes()).status_code == 200
    after = counts()
    assert after["media"] == before["media"] + 1 and after["jobs"] == before["jobs"] + 1
