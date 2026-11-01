"""Offline provider-contract and conservative filter tests; these do not establish live SQL or provider behavior."""

import json
from types import SimpleNamespace

import pytest
from luma.core.errors import DomainError
from luma.features.catalog.criteria import query_constraints
from luma.features.catalog.schemas import CatalogSearch
from luma.features.catalog.semantic import vector_literal
from luma_agent.adapters import embeddings
from pydantic import SecretStr


def unit_vector(axis=0):
    """Return a normalized deterministic fixture vector, never a semantic model result."""
    values = [0.0] * 1536
    values[axis] = 1.0
    return values


@pytest.mark.parametrize("case", ["short", "zero", "nan", "infinity", "boolean", "oversized"])
def test_invalid_provider_vectors_fail_closed(case):
    """Wrong dimensions, unsupported values and empty evidence cannot enter a pgvector parameter."""
    values = unit_vector()
    if case == "short":
        values = values[:-1]
    elif case == "zero":
        values = [0.0] * 1536
    elif case == "nan":
        values[0] = float("nan")
    elif case == "infinity":
        values[0] = float("inf")
    elif case == "boolean":
        values[0] = True
    else:
        values[0] = 2.0
    with pytest.raises(DomainError):
        vector_literal(values)


def test_valid_vector_has_only_finite_numeric_json():
    """Validated provider values serialize as data rather than SQL syntax."""
    assert json.loads(vector_literal(unit_vector())) == unit_vector()


@pytest.mark.parametrize(
    "query",
    ["not IP44 downlights", "downlights 18W or 30W", "downlights 3000K or 4000K", "avoid DL-001", "   "],
)
def test_shared_filters_refuse_ambiguous_or_negated_requirements(query):
    """Semantic matching must not silently relax conditions already rejected by the lexical baseline."""
    assert query_constraints(CatalogSearch(query=query)) is None


def test_shared_filters_keep_explicit_model_and_specs():
    """An explicit model remains exact even when descriptive text would produce other candidates."""
    criteria = query_constraints(CatalogSearch(query="Please quote DL-001 downlights 18W 4000K IP44"))
    assert criteria.codes == ["DL-001"]
    assert (criteria.watts, criteria.cct, criteria.ip_rating) == (18, 4000, "IP44")
    assert query_constraints(CatalogSearch(query="downlights 18W", watts=30)) is None


@pytest.mark.parametrize("duplicate", [False, True])
def test_embedding_response_indices_bind_each_vector_to_its_requested_record(monkeypatch, duplicate):
    """Reordered results are correlated correctly; duplicated/missing indices cannot publish the wrong product evidence."""
    calls = []

    class FakeClient:
        """Emulate only the external response boundary while exercising real input/vector validation."""

        def __init__(self, **kwargs):
            """Expose the pinned embeddings method without reading credentials or opening a connection."""
            self.embeddings = self

        def __enter__(self):
            """Enter the local fake context used by the actual adapter's resource lifecycle."""
            return self

        def __exit__(self, *args):
            """Close the fake context without suppressing contract failures."""
            return False

        def create(self, **kwargs):
            """Return deterministic vectors with deliberately reordered or invalid record indices."""
            calls.append(kwargs)
            return SimpleNamespace(
                data=[
                    SimpleNamespace(index=0 if duplicate else 1, embedding=unit_vector(1)),
                    SimpleNamespace(index=0, embedding=unit_vector()),
                ],
                usage=SimpleNamespace(total_tokens=10),
            )

    monkeypatch.setattr(embeddings, "OpenAI", FakeClient)
    config = SimpleNamespace(
        embedding_model="text-embedding-3-small", openai_api_key=SecretStr("unit-only-no-network")
    )
    if duplicate:
        with pytest.raises(DomainError):
            embeddings.embed_texts(config, ["first", "second"])
    else:
        vectors, estimate = embeddings.embed_texts(config, ["first", "second"])
        assert vectors == [unit_vector(), unit_vector(1)] and estimate > 0
    assert calls[0]["dimensions"] == 1536 and calls[0]["encoding_format"] == "float"
