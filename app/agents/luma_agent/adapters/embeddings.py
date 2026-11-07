"""Bounded fixed-model embedding calls without automatic retries; traced (masked) only inside a worker job trace."""

from decimal import Decimal

from luma.core.errors import DomainError
from luma.features.catalog.semantic import vector_literal
from openai import OpenAI

from ..observability import masked_or_off, model_call, set_outputs, set_usage


def validate_embedding_provider(config):
    """Require the explicitly verified model/key before reserving an embedding operation."""
    if config.embedding_model != "text-embedding-3-small" or not config.openai_api_key.get_secret_value():
        raise DomainError("The configured embedding model/key has not been verified.", 503)


def embed_texts(config, texts: list[str]) -> tuple[list[list[float]], Decimal]:
    """Make one bounded request and validate vector dimensions/index correlation before returning an estimate.

    Limits are at most 500 nonempty inputs, 8000 UTF-8 bytes each and 100000 bytes
    overall. They conservatively bound this English catalog/query workload below
    the provider token ceilings. Inside a job trace the input texts, vector count, dimensions
    and token usage are traced (masked); the vectors themselves are not exported.
    """
    validate_embedding_provider(config)
    if (
        not texts
        or len(texts) > 500
        or any(not text.strip() or len(text.encode()) > 8000 for text in texts)
        or sum(len(text.encode()) for text in texts) > 100000
    ):
        raise DomainError("The embedding input exceeds its bounded policy.", 422)
    with (
        OpenAI(api_key=config.openai_api_key.get_secret_value(), timeout=35, max_retries=0) as client,
        masked_or_off(),
        model_call("openai.embeddings", config.embedding_model, {"input": texts}) as call,
    ):
        response = client.embeddings.create(
            model=config.embedding_model, input=texts, dimensions=1536, encoding_format="float"
        )
        set_usage(
            call,
            input_tokens=response.usage.total_tokens,
            input_usd_per_million=0.02,
        )
        set_outputs(
            call,
            {
                "vectors": len(response.data),
                "dimensions": 1536,
                "usage": {"total_tokens": response.usage.total_tokens},
            },
        )
    indexed = {item.index: item.embedding for item in response.data}
    if len(response.data) != len(texts) or set(indexed) != set(range(len(texts))):
        raise DomainError("Embedding results did not match the requested records.", 503)
    vectors = [indexed[index] for index in range(len(texts))]
    for vector in vectors:
        vector_literal(vector)
    estimate = Decimal(response.usage.total_tokens) * Decimal("0.02") / 1000000
    return vectors, estimate
