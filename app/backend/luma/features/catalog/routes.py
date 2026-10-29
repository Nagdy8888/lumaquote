from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import Response

from luma.core.admission import rate_limit
from luma.core.database import database
from luma.core.errors import DomainError
from luma.core.http import Staff
from luma.core.identity import membership
from luma.core.storage import get_file

from .retrieval import search_catalog
from .schemas import CatalogHit, CatalogSearch

router = APIRouter()


@router.post("/api/catalog/search", response_model=list[CatalogHit])
def search(body: CatalogSearch, user: Staff):
    """Retrieve company-scoped descriptive candidates with source versions/pages, without calculating commercial terms."""
    with database(user) as conn:
        member = membership(conn, user)
        rate_limit(conn, f"{user}:read", 120)
        rate_limit(conn, f"{user}:catalog_search", 30)
        return search_catalog(conn, member["company_id"], body)


@router.get("/api/sources/{sid}/pdf")
def source_pdf(sid: UUID, user: Staff):
    """Authorize a catalog source and stream its private original PDF without exposing Storage credentials or URLs."""
    with database(user) as conn:
        member = membership(conn, user)
        row = conn.execute(
            "select * from luma.sources where id=%s and company_id=%s", (sid, member["company_id"])
        ).fetchone()
        if not row:
            raise DomainError("Source not found.", 404)
        content = get_file(row["object_path"])
        if content is None:
            raise DomainError("Source file unavailable.", 404)
        return Response(content, media_type="application/pdf")
