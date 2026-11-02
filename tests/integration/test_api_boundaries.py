"""Staff API authentication, CORS, response-header, size and rate-limit boundaries against the real app and Auth."""

import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from luma.core.config import settings
from luma.google_gateway import app as gateway
from luma.main import app
from test_manual_workflow import post

ALLOWED = "http://127.0.0.1:5173"


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer"},
        {"Authorization": "Basic dXNlcjpwYXNz"},
        {"Authorization": "Bearer not-a-jwt"},
        {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR9.e30.forged"},
    ],
    ids=["missing", "empty-bearer", "wrong-scheme", "garbage", "forged-jwt"],
)
def test_missing_or_invalid_credentials_never_reach_business_code(environment, headers):
    """Absent, malformed and forged bearer credentials are refused before any company data is read."""
    with TestClient(app) as client:
        for path in ("/api/workspace", f"/api/conversations/{uuid4()}"):
            response = client.get(path, headers=headers)
            assert response.status_code in (401, 403), (path, response.status_code)
            assert "company" not in response.text.lower() and "customer" not in response.text.lower()


def test_auth_outage_is_a_safe_503_not_an_open_door(environment, monkeypatch):
    """When Supabase Auth is unreachable the API fails closed with 503 and no data."""
    monkeypatch.setenv("SUPABASE_URL", "http://127.0.0.1:9")
    settings.cache_clear()
    with TestClient(app) as client:
        response = client.get("/api/workspace", headers=environment["headers"])
    assert response.status_code == 503 and "conversation" not in response.text.lower()


def test_cors_allows_only_the_exact_local_origins(environment):
    """A foreign origin gets no CORS grant on preflight or simple requests; the app origin does."""
    with TestClient(app) as client:
        ok = client.options(
            "/api/conversations",
            headers={
                "Origin": ALLOWED,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,idempotency-key",
            },
        )
        assert ok.status_code == 200 and ok.headers["access-control-allow-origin"] == ALLOWED
        assert "access-control-allow-credentials" not in ok.headers
        for origin in (
            "https://evil.example",
            "http://127.0.0.1:5173.evil.example",
            "null",
            "http://localhost:5174",
            "https://127.0.0.1:5173",
        ):
            denied = client.options(
                "/api/conversations", headers={"Origin": origin, "Access-Control-Request-Method": "POST"}
            )
            assert "access-control-allow-origin" not in denied.headers, origin
            simple = client.get("/api/health", headers={"Origin": origin})
            assert "access-control-allow-origin" not in simple.headers, origin
        bad_method = client.options(
            "/api/conversations", headers={"Origin": ALLOWED, "Access-Control-Request-Method": "DELETE"}
        )
        assert bad_method.status_code == 400
        bad_header = client.options(
            "/api/conversations",
            headers={
                "Origin": ALLOWED,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "x-service-role",
            },
        )
        assert bad_header.status_code == 400


@pytest.mark.parametrize("target", ["api", "gateway"])
def test_every_response_is_private_nosniff_and_unframed(environment, target):
    """Both processes mark responses no-store, nosniff, no-referrer and X-Frame-Options DENY, including errors."""
    client = TestClient(app if target == "api" else gateway)
    with client:
        for path in ("/api/health", "/api/conversations", "/missing-route"):
            response = client.get(path)
            for name, value in {
                "cache-control": "no-store",
                "x-content-type-options": "nosniff",
                "referrer-policy": "no-referrer",
                "x-frame-options": "DENY",
            }.items():
                assert response.headers.get(name) == value, (target, path, name)


def test_private_pdf_is_never_cacheable(environment):
    """An authorized PDF response carries no-store, so browsers and proxies keep no copy."""
    from test_manual_workflow import create_request, make_draft

    cid = create_request(environment)
    quote = make_draft(environment, cid)
    environment["files"].append(f"{environment['company']}/quotes/{quote['id']}.pdf")
    response = environment["api"].get(f"/api/quotes/{quote['id']}/pdf", headers=environment["headers"])
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"].startswith("application/pdf")


def test_declared_oversize_and_malformed_length_are_rejected_before_routing(environment):
    """A Content-Length above 11 MiB or a non-numeric one is a 413 even for an unauthenticated caller."""
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/conversations", content=b"x", headers={"Content-Length": str(11 * 1024 * 1024 + 1)}
            ).status_code
            == 413
        )
        assert client.get("/api/health", headers={"Content-Length": "abc"}).status_code == 413


def test_gateway_never_exposes_staff_routes_or_documentation(environment):
    """The tunnel-facing app has only signed callbacks and the webhook: no staff API, no docs, no schema."""
    with TestClient(gateway) as client:
        for path in (
            "/api/workspace",
            "/api/conversations",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/health",
        ):
            assert client.get(path).status_code == 404, path
        for path in (
            "/callbacks/google/snapshot",
            "/callbacks/google",
            "/callbacks/google/exports/claim",
            "/callbacks/google/exports/receipt",
            "/webhooks/whatsapp",
        ):
            assert client.post(path, content=b"{}").status_code != 404, (
                path
            )  # exists, and refuses unsigned bodies


def test_mutation_rate_limit_rejects_the_thirty_first_request_with_retry_guidance(environment):
    """The shared per-user minute window admits 30 mutations; the next is a 429 with Retry-After."""
    env = environment
    # The window is a fixed per-minute bucket; start early in a minute so 31 requests cannot straddle it.
    while time.time() % 60 > 25:
        time.sleep(1)
    statuses = [
        post(env, "/conversations", {"customer_name": f"Rate {n}", "text": "3 DL-001"}).status_code
        for n in range(31)
    ]
    assert statuses[:30] == [200] * 30 and statuses[30] == 429
    denied = env["api"].post(
        "/api/conversations",
        headers={**env["headers"], "Idempotency-Key": str(uuid4())},
        json={"customer_name": "Again", "text": "3 DL-001"},
    )
    assert denied.status_code == 429 and denied.headers["retry-after"] == "60"
