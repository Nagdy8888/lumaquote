"""Canonical PDF checks against real local private Storage and staff authorization."""

from io import BytesIO

import httpx
from luma.core.config import settings
from pypdf import PdfReader
from test_manual_workflow import create_request, make_draft


def test_pdf_uses_persisted_revision_and_stable_private_bytes(environment):
    """Review/export returns identical canonical bytes with independently expected money and no public caching."""
    env = environment
    cid = create_request(env)
    quote = make_draft(env, cid)
    # Customer labels may change independently; PDF content must retain the
    # customer identity that staff actually reviewed in this immutable revision.
    import psycopg

    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "update luma.conversations set customer_name=%s where id=%s and company_id=%s",
            ("Changed after review", cid, env["company"]),
        )
    path = f"/api/quotes/{quote['id']}/pdf"
    response = env["api"].get(path, headers=env["headers"])
    assert response.status_code == 200
    env["files"].append(f"{env['company']}/quotes/{quote['id']}.pdf")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"].startswith("application/pdf")
    pages = PdfReader(BytesIO(response.content)).pages
    assert len(pages) == 1
    text = pages[0].extract_text()
    assert all(
        value in text
        for value in ("DL-001", "97.05", "Revision 1", "Tax excluded", "Synthetic test customer")
    )
    assert "Changed after review" not in text
    assert "(Cairo)" in text
    second = env["api"].get(path, headers=env["headers"])
    assert second.content == response.content
    assert env["api"].get(path).status_code in (401, 403)
    config = settings()
    anonymous = httpx.get(
        config.supabase_url + f"/storage/v1/object/luma-private/{env['files'][0]}",
        headers={"apikey": config.supabase_anon_key.get_secret_value()},
        timeout=5,
    )
    assert anonymous.status_code in (400, 401, 403, 404)
