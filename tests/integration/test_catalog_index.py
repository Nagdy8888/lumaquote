"""Real index publication and uncertain-outcome accounting with the provider boundary replaced."""

from decimal import Decimal
from uuid import uuid4

import psycopg
import pytest
from luma.core.errors import DomainError
from luma_agent.runtime import catalog_index
from psycopg.rows import dict_row


@pytest.mark.parametrize("lost", [False, True])
def test_operator_index_settles_or_blocks_uncertain_retries(environment, monkeypatch, lost):
    """Actual DB reservations/publication survive a simulated lost response without another provider attempt."""
    env = environment
    calls = []

    def fake_embedding(config, texts):
        """Record one provider boundary crossing, returning deterministic vectors or a simulated uncertain outcome."""
        calls.append(len(texts))
        if lost:
            raise TimeoutError("Synthetic lost embedding response")
        return [[1.0] + [0.0] * 1535 for _ in texts], Decimal("0.00001")

    monkeypatch.setattr(catalog_index, "embed_texts", fake_embedding)
    monkeypatch.setattr(catalog_index, "validate_embedding_provider", lambda config: None)
    run = uuid4()
    if lost:
        with pytest.raises(TimeoutError):
            catalog_index.index_company(env["company"], run)
        with pytest.raises(DomainError, match="reconciliation"):
            catalog_index.index_company(env["company"], uuid4())
    else:
        result = catalog_index.index_company(env["company"], run)
        assert result["records"] == 3 and result["actual_billing"] == "not retrieved"
        with pytest.raises(DomainError, match="reconciliation"):
            catalog_index.index_company(env["company"], run)
    assert calls == [3]
    with psycopg.connect(env["dsn"], row_factory=dict_row) as conn:
        usage = conn.execute("select status,estimated from luma.usage where job_id=%s", (run,)).fetchone()
        assert usage["status"] == ("unknown" if lost else "settled")
        count = conn.execute(
            "select count(*) n from luma.catalog_embeddings where company_id=%s", (env["company"],)
        ).fetchone()["n"]
        assert count == (0 if lost else 3)
