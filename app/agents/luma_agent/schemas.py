from luma.core.contracts import StrictModel
from pydantic import Field, StrictInt


class RequestedLine(StrictModel):
    """Untrusted model extraction of an explicit SKU and quantity; neither field establishes catalog truth."""

    sku: str | None
    quantity: StrictInt | None = Field(ge=1, le=10000)


class Extraction(StrictModel):
    """Bounded untrusted model output consumed by deterministic confirmation policy.

    At most 20 requested lines carry nullable explicit fields; missing/uncertain
    consequential values must lead to clarification. The model's clarification
    prose is not outbound commercial authority: requirements.clarification_for
    chooses fixed safe wording. Valid structure does not prove a SKU exists,
    quantity is available, price is current or a quotation is approved.
    """

    lines: list[RequestedLine] = Field(max_length=20)
    clarification: str | None
    uncertain_critical_fields: bool
