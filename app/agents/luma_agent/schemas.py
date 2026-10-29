from luma.core.contracts import StrictModel
from pydantic import Field, StrictInt


class RequestedLine(StrictModel):
    """Untrusted model extraction of an explicit SKU and quantity; neither field establishes catalog truth."""

    sku: str | None
    quantity: StrictInt | None = Field(ge=1, le=10000)


class Extraction(StrictModel):
    """Typed model result carrying explicit product requests and consequential uncertainty for clarification."""

    lines: list[RequestedLine] = Field(max_length=20)
    clarification: str | None
    uncertain_critical_fields: bool
