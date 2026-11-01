"""Real-database callback verification with isolated synthetic company data."""

import hashlib
import hmac
import json
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.google_gateway import app


def test_signed_callback_receipts(environment, monkeypatch):
    """Reject forged/stale/cross-company events and persist concurrent duplicates exactly once."""
    company = str(environment["company"])
    monkeypatch.setenv("GOOGLE_COMPANY_ID", company)
    monkeypatch.setenv("GOOGLE_SHEET_ID", "synthetic-workbook")
    monkeypatch.setenv("GOOGLE_CALLBACK_SECRET", "test-only-callback-key-" + "x" * 32)
    settings.cache_clear()
    secret = settings().google_callback_secret.get_secret_value()
    hint = dict(
        schema_version=1,
        company_id=company,
        spreadsheet_id="synthetic-workbook",
        timestamp=int(time.time()),
        nonce=str(uuid4()),
        event="supplier_records_changed",
    )

    def post(value, valid=True):
        """Send a signed fixture through the real callback gateway without external HTTP traffic."""
        body = json.dumps(value).encode()
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest() if valid else "0" * 64
        with TestClient(app) as client:
            return client.post("/callbacks/google", content=body, headers={"X-Luma-Signature": signature})

    assert post(hint, False).status_code == 401
    assert post({**hint, "company_id": str(uuid4())}).status_code == 403
    assert post({**hint, "timestamp": int(time.time()) - 600}).status_code == 401
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(post, [hint] * 4))
    assert [r.status_code for r in results] == [202] * 4
    assert post({**hint, "timestamp": hint["timestamp"] + 1}).status_code == 409
    with TestClient(app) as client:
        assert client.get("/api/workspace").status_code == 404
        assert client.get("/docs").status_code == 404
        assert client.post("/callbacks/google", content=b"x" * 4097).status_code == 413
    with psycopg.connect(settings().database_url.get_secret_value()) as conn:
        assert (
            conn.execute(
                "select count(*) from luma.google_edit_receipts where company_id=%s", (company,)
            ).fetchone()[0]
            == 1
        )
        assert (
            conn.execute(
                "select count(*) from luma.google_refresh_signals where company_id=%s", (company,)
            ).fetchone()[0]
            == 1
        )
