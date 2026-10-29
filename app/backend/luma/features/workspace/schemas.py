"""Public read models shared with the generated TypeScript API client."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CompanyView(BaseModel):
    """Authorized company identity and the honest synthetic-data disclosure."""

    id: UUID
    name: str
    synthetic: bool


class ConversationView(BaseModel):
    """Staff-visible request state; version is the optimistic mutation precondition."""

    id: UUID
    company_id: UUID
    customer_name: str
    customer_company: str
    recipient: str
    channel: str
    owner: str
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    last_customer_at: datetime
    preview: str | None = None


class ProductView(BaseModel):
    """Validated catalog and commercial snapshot fields; embeddings are never sent to the UI."""

    id: UUID
    sku: str
    name: str
    family: str
    description: str
    watts: int
    lumens: int
    cct: int
    ip_rating: str
    price: Decimal
    available: int
    pack_size: int
    discontinued: bool
    source_id: UUID
    page: int
    snapshot_id: UUID


class SourceView(BaseModel):
    """An authorized catalog reference without its private Storage path."""

    id: UUID
    title: str
    version: int
    created_at: datetime


class QuoteLineView(BaseModel):
    """Canonical persisted line used identically in review and PDF output."""

    product_id: UUID
    sku: str
    name: str
    quantity: int
    unit: str
    unit_price: str
    line_total: str
    source_id: UUID
    page: int


class QuoteContentView(BaseModel):
    """Server-calculated totals and terms; browser inputs never determine the monetary result."""

    lines: list[QuoteLineView]
    currency: str
    tax: str
    subtotal: str
    discount_percent: str
    discount: str
    shipping: str
    total: str
    terms: str
    stock_reserved: bool
    customer_name: str
    customer_company: str


class QuoteView(BaseModel):
    """An immutable quotation revision and its separately observed delivery summary."""

    id: UUID
    conversation_id: UUID
    number: str
    revision: int
    status: str
    content: QuoteContentView
    valid_until: datetime
    created_at: datetime
    customer_name: str | None = None
    customer_company: str | None = None
    delivery: str | None = None


class MessageView(BaseModel):
    """Plain text or an authorized media reference; never a public raw-file capability."""

    id: UUID
    actor: str
    kind: str
    body: str
    created_at: datetime


class DeliveryView(BaseModel):
    """Durable delivery outcome; provider submission and customer delivery remain distinct."""

    id: UUID
    kind: str
    status: str
    error_code: str | None
    updated_at: datetime


class ConversationDetail(BaseModel):
    """Canonical inbox detail returned after authorization and current membership checks."""

    conversation: ConversationView
    messages: list[MessageView]
    quote: QuoteView | None
    delivery: list[DeliveryView]


class ActivityView(BaseModel):
    """Consequential event summary; private audit details are not part of the read contract."""

    id: int
    action: str
    resource_id: UUID | None
    created_at: datetime


class JobView(BaseModel):
    """A bounded job status with a safe failure code, excluding provider payloads."""

    id: UUID
    conversation_id: UUID
    kind: str
    status: str
    error_code: str | None


class UsageView(BaseModel):
    """Estimated plus reserved allowance, explicitly distinct from provider-billed cost."""

    estimated_or_reserved: Decimal


class WorkspaceView(BaseModel):
    """Validated workspace response consumed by the generated frontend contracts."""

    company: CompanyView
    role: str
    conversations: list[ConversationView]
    quotes: list[QuoteView]
    products: list[ProductView]
    sources: list[SourceView]
    activity: list[ActivityView]
    jobs: list[JobView]
    usage: UsageView
    integrations: dict[str, str]
