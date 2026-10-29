"""Real PostgreSQL descriptive evidence lookup and source freshness at commercial boundaries."""

from uuid import uuid4

import psycopg
import pytest
from luma.core.database import database
from luma.features.catalog.retrieval import search_catalog
from luma.features.catalog.schemas import CatalogSearch
from luma_agent.runtime.delivery import deliver_one
from test_manual_workflow import create_request, get_detail, make_draft, post


def search(env, query, **filters):
    """Call the actual authenticated lookup route; never supply company authority from client input."""
    response = env["api"].post(
        "/api/catalog/search", headers=env["headers"], json={"query": query, **filters}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_exact_sku_precedes_descriptive_similarity(environment):
    """An explicit model restricts lookup to that exact code; a missing code cannot become a near-model substitute."""
    assert [hit["sku"] for hit in search(environment, "Please quote DL-001 downlights")] == ["DL-001"]
    assert search(environment, "DL-999 downlights") == []


def test_description_lookup_retains_original_page_version_and_explicit_specs(environment):
    """Descriptive requests produce current citations while conflicting wattage or negation remains unresolved."""
    hits = search(environment, "I need downlights 18W 4000K IP44")
    assert hits and len(hits) <= 5
    assert all(
        hit["source_id"] == str(environment["source"]) and hit["source_version"] == 1 and hit["page"] == 1
        for hit in hits
    )
    assert all("price" not in hit and "available" not in hit for hit in hits)
    assert search(environment, "downlights 30W") == []
    assert search(environment, "downlights 18W or 30W") == []
    assert search(environment, "not IP44 downlights") == []
    assert search(environment, "downlights 18W", watts=30) == []


def test_authoritative_family_is_searchable_when_name_uses_different_words(environment):
    """Supplier-owned family evidence must participate even when the model name uses an equivalent category label."""
    env = environment
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute(
            "update luma.products set family='Exterior fixtures',name='Weather-resistant floodlight' where id=%s",
            (env["products"][0],),
        )
    assert [hit["sku"] for hit in search(env, "Exterior fixtures 18W 4000K IP44")] == ["DL-001"]


def test_lookup_is_tenant_scoped_and_cannot_accept_client_authority(environment):
    """An arbitrary company identity sees no rows even when querying a known SKU through the restricted role."""
    env = environment
    with database(env["user"]) as conn:
        assert search_catalog(conn, uuid4(), CatalogSearch(query="DL-001")) == []
    assert env["api"].post("/api/catalog/search", json={"query": "DL-001"}).status_code in (401, 403)
    assert (
        env["api"]
        .post(
            "/api/catalog/search",
            headers=env["headers"],
            json={"query": "DL-001", "company_id": str(uuid4())},
        )
        .status_code
        == 422
    )


@pytest.mark.parametrize("approved", [False, True])
def test_retired_catalog_cannot_be_recommended_or_finalized(environment, approved):
    """Evidence retirement excludes new matches/drafts and blocks existing approval or queued dispatch."""
    env = environment
    cid = create_request(env)
    make_draft(env, cid)
    if approved:
        assert (
            post(
                env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
            ).status_code
            == 200
        )
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute("update luma.sources set retired_at=now() where id=%s", (env["source"],))
    assert search(env, "DL-001") == []
    current = get_detail(env, cid)
    assert (
        post(
            env,
            f"/conversations/{cid}/draft",
            {
                "expected_version": current["conversation"]["version"],
                "lines": [{"product_id": str(env["products"][0]), "quantity": 3}],
            },
        ).status_code
        == 422
    )
    if approved:
        assert deliver_one(env["company"])
        assert get_detail(env, cid)["delivery"][0]["status"] == "blocked"
    else:
        assert (
            post(
                env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
            ).status_code
            == 409
        )


@pytest.mark.parametrize("changed", ["source", "price"])
def test_changed_product_evidence_requires_another_review(environment, changed):
    """A new technical source or out-of-band commercial change cannot retain old approval eligibility."""
    env = environment
    cid = create_request(env)
    make_draft(env, cid)
    with psycopg.connect(env["dsn"]) as conn:
        if changed == "source":
            replacement = uuid4()
            conn.execute(
                "insert into luma.sources(id,company_id,title,version,object_path) values(%s,%s,'Synthetic replacement',2,%s)",
                (replacement, env["company"], f"{env['company']}/catalogs/replacement.pdf"),
            )
            conn.execute(
                "update luma.products set source_id=%s where id=%s", (replacement, env["products"][0])
            )
            assert (
                search(env, "DL-001")[0]["source_version"] == 1
            )  # Other connection cannot see this uncommitted edit.
        else:
            conn.execute("update luma.products set price=price+1 where id=%s", (env["products"][0],))
    if changed == "source":
        assert search(env, "DL-001")[0]["source_version"] == 2
    assert (
        post(
            env, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"}
        ).status_code
        == 409
    )
