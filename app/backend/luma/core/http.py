from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .errors import DomainError

bearer = HTTPBearer()
_auth_client: httpx.Client | None = None


def auth_client() -> httpx.Client:
    """Return the process-wide HTTP client used to verify staff bearer tokens, creating it on first use.

    A fresh `httpx.get` builds a new client and TLS context per call, which cost about 0.25-0.55 s
    per request on the Windows development machine (measured 2026-11-08) and starved the 120-reads
    per minute test; a shared client reuses connections and answers in about 4 ms. The client has
    no base URL, credentials or cookies, so every call still passes its own headers. Thread-safe.
    """
    global _auth_client
    if _auth_client is None:
        _auth_client = httpx.Client(timeout=5)
    return _auth_client


async def domain_error(request: Request, exc: DomainError):
    """Translate a safe business rejection into a bounded JSON response and rate-limit retry guidance."""
    return JSONResponse(
        {"detail": exc.message},
        status_code=exc.status,
        headers={"Retry-After": "60"} if exc.status == 429 else None,
    )


async def dependency_unavailable(request: Request, exc: Exception):
    """Answer a retryable 503 when PostgreSQL or Storage cannot be reached, hiding hosts, ports and credentials.

    Covers `psycopg.OperationalError` and `httpx.TransportError` raised inside a route. The request
    transaction has already rolled back, so nothing is half-written; callers retry with the same
    idempotency key. The exception text is never returned or logged here because connection errors
    can echo a DSN. Authentication outages keep their own 503 in `staff`.
    """
    return JSONResponse(
        {"detail": "A required service is temporarily unavailable. Try again shortly."},
        status_code=503,
        headers={"Retry-After": "30"},
    )


async def response_boundaries(request: Request, call_next):
    """Reject oversized declared requests and attach private-cache, content-type, referrer, and framing controls."""
    length = request.headers.get("content-length", "0")
    if not length.isdigit() or int(length) > 11 * 1024 * 1024:
        return JSONResponse({"detail": "Request too large."}, status_code=413)
    response = await call_next(request)
    response.headers.update(
        {
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "X-Frame-Options": "DENY",
        }
    )
    return response


def staff(credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]):
    """Validate the bearer token with local Supabase Auth; return its verified user ID, never self-reported metadata."""
    config = settings()
    try:
        response = auth_client().get(
            f"{config.supabase_url}/auth/v1/user",
            headers={
                "apikey": config.supabase_anon_key.get_secret_value(),
                "Authorization": f"Bearer {credentials.credentials}",
            },
        )
        if response.status_code != 200:
            raise DomainError("Your staff session is invalid or expired.", 401)
        uid = str(UUID(response.json()["id"]))
    except (httpx.HTTPError, KeyError, ValueError):
        raise DomainError("Staff authentication is temporarily unavailable.", 503) from None
    return uid


Staff = Annotated[str, Depends(staff)]
OperationKey = Annotated[UUID, Header(alias="Idempotency-Key")]
