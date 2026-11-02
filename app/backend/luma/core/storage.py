import httpx

from .config import settings


def storage_headers():
    """Build backend-only Storage credentials; callers must scope the object before performing file I/O."""
    secret = settings().supabase_service_role_key.get_secret_value()
    return {"apikey": secret, "Authorization": f"Bearer {secret}"}


def put_file(path: str, data: bytes, content_type: str):
    """Create a private immutable object; tolerate an existing canonical object without overwriting it."""
    with httpx.Client(timeout=20) as client:
        response = client.post(
            f"{settings().supabase_url}/storage/v1/object/luma-private/{path}",
            headers={**storage_headers(), "Content-Type": content_type, "x-upsert": "false"},
            content=data,
        )
        if response.status_code not in (200, 201) and "Duplicate" not in response.text:
            response.raise_for_status()


def get_file(path: str) -> bytes | None:
    """Read a server-selected private object, returning None when missing and propagating other Storage failures."""
    with httpx.Client(timeout=20) as client:
        response = client.get(
            f"{settings().supabase_url}/storage/v1/object/luma-private/{path}", headers=storage_headers()
        )
        if response.status_code in (400, 404):
            return None
        response.raise_for_status()
        return response.content


def delete_files(company: str, paths: list[str]) -> int:
    """Delete private objects belonging to one company; every path must start with that company's prefix.

    Used only by the operator retention tool. The prefix check is a guard against a bug selecting
    another tenant's object, not an authorization mechanism. Missing objects are not an error, so a
    repeated or interrupted purge can simply be run again. Returns the number of paths requested.
    """
    if not paths:
        return 0
    if any(not path.startswith(f"{company}/") or ".." in path for path in paths):
        raise ValueError("Refusing to delete objects outside the company prefix.")
    with httpx.Client(timeout=30) as client:
        for start in range(0, len(paths), 100):
            response = client.request(
                "DELETE",
                f"{settings().supabase_url}/storage/v1/object/luma-private",
                headers=storage_headers(),
                json={"prefixes": paths[start : start + 100]},
            )
            response.raise_for_status()
    return len(paths)
