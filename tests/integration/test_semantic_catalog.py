"""Actual pgvector scope/freshness contracts using deterministic vectors, without paid calls."""

from uuid import uuid4

import psycopg
import pytest
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.catalog.schemas import CatalogSearch
from luma.features.catalog.semantic import (
    embedding_inputs,
    has_current_embeddings,
    publish_embeddings,
    semantic_search,
)
from psycopg.rows import dict_row


def publish_fixture(conn, company):
    """Publish identical unit vectors for the fixture's current descriptive records only."""
    records = embedding_inputs(conn, company)
    vector = [1.0] + [0.0] * 1535
    publish_embeddings(conn, company, records, [vector] * len(records))
    return vector


def test_semantic_candidates_obey_scope_specs_and_exact_codes(environment):
    """Similarity cannot replace explicit model codes, violate specs, or return another tenant's records."""
    env = environment
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        vector = publish_fixture(conn, env["company"])
    with database(env["user"]) as conn:
        hits = semantic_search(
            conn, env["company"], CatalogSearch(query="ceiling fixtures 18W 4000K"), vector
        )
        assert len(hits) == 3
        assert all(hit.source_id == env["source"] and hit.page == 1 for hit in hits)
        assert semantic_search(conn, uuid4(), CatalogSearch(query="ceiling fixtures"), vector) == []
        assert (
            semantic_search(conn, env["company"], CatalogSearch(query="ceiling fixtures 30W"), vector) == []
        )
        assert semantic_search(conn, env["company"], CatalogSearch(query="DL-999"), vector) == []
        assert [
            hit.sku for hit in semantic_search(conn, env["company"], CatalogSearch(query="DL-001"), vector)
        ] == ["DL-001"]
        assert (
            semantic_search(
                conn, env["company"], CatalogSearch(query="ceiling fixtures"), [0.0, 1.0] + [0.0] * 1534
            )
            == []
        )


@pytest.mark.parametrize("change", ["version", "page", "content", "retired", "discontinued"])
def test_semantic_cache_excludes_stale_evidence(environment, change):
    """A changed source, record, page or active status invalidates cached candidates immediately."""
    env = environment
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        vector = publish_fixture(conn, env["company"])
        assert has_current_embeddings(conn, env["company"])
        if change == "version":
            conn.execute("update luma.sources set version=version+1 where id=%s", (env["source"],))
        elif change == "retired":
            conn.execute("update luma.sources set retired_at=now() where id=%s", (env["source"],))
        elif change == "page":
            conn.execute("update luma.products set page=page+1 where company_id=%s", (env["company"],))
        elif change == "content":
            conn.execute(
                "update luma.products set description='Replacement technical evidence' where company_id=%s",
                (env["company"],),
            )
        else:
            conn.execute("update luma.products set discontinued=true where company_id=%s", (env["company"],))
        assert not has_current_embeddings(conn, env["company"])
        assert semantic_search(conn, env["company"], CatalogSearch(query="ceiling fixtures"), vector) == []


def test_index_publication_rejects_changed_input(environment):
    """An edit during provider work aborts publication rather than attaching vectors to newer evidence."""
    env = environment
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        records = embedding_inputs(conn, env["company"])
        conn.execute("update luma.products set page=page+1 where company_id=%s", (env["company"],))
        with pytest.raises(DomainError, match="changed during indexing"):
            publish_embeddings(conn, env["company"], records, [[1.0] + [0.0] * 1535] * len(records))
        assert not has_current_embeddings(conn, env["company"])
