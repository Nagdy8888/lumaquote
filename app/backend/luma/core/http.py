from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .errors import DomainError

bearer = HTTPBearer()


async def domain_error(request: Request, exc: DomainError):
    """Translate a safe business rejection into a bounded JSON response and rate-limit retry guidance."""
    return JSONResponse(
        {"detail": exc.message},
        status_code=exc.status,
        headers={"Retry-After": "60"} if exc.status == 429 else None,
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
        response = httpx.get(
            f"{config.supabase_url}/auth/v1/user",
            timeout=5,
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
