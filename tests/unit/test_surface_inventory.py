"""The exposed HTTP surface equals the reviewed inventory, so a new or unauthenticated route fails loudly.

Reviewed in `docs/reference/BACKEND.md` (surface inventory). The staff API is local-only and never tunneled; the
signed gateway is the only process meant to be reachable from the internet and carries no staff route.
"""

from luma.google_gateway import app as gateway
from luma.main import app as staff

STAFF_OPERATIONS = {
    "GET /api/health",
    "GET /api/workspace",
    "GET /api/events",
    "GET /api/conversations/{cid}",
    "POST /api/conversations",
    "POST /api/conversations/{cid}/audio",
    "POST /api/conversations/{cid}/customer-reply",
    "POST /api/conversations/{cid}/decision",
    "POST /api/conversations/{cid}/draft",
    "POST /api/conversations/{cid}/image",
    "POST /api/conversations/{cid}/messages",
    "POST /api/conversations/{cid}/ownership",
    "POST /api/conversations/{cid}/reply",
    "GET /api/media/{mid}/audio",
    "GET /api/media/{mid}/image",
    "GET /api/quotes/{qid}/pdf",
    "GET /api/sources/{sid}/pdf",
    "POST /api/catalog/search",
    # D49 stock, orders and purchasing (task T4). Administrator-only writes are enforced in services.
    "GET /api/inventory/stock",
    "GET /api/inventory/movements",
    "POST /api/inventory/adjustments",
    "POST /api/inventory/reorder-levels",
    "GET /api/inventory/alerts",
    "POST /api/inventory/alerts/{alert_id}/acknowledge",
    "GET /api/orders",
    "POST /api/orders/{order_id}/confirm",
    "POST /api/orders/{order_id}/cancel",
    "GET /api/purchase-orders",
    "POST /api/purchase-orders",
    "POST /api/purchase-orders/{order_id}/receive",
    "POST /api/purchase-orders/{order_id}/cancel",
}
GATEWAY_OPERATIONS = {
    "POST /callbacks/google",
    "POST /callbacks/google/snapshot",
    "POST /callbacks/google/exports/claim",
    "POST /callbacks/google/exports/receipt",
    "GET /webhooks/whatsapp",
    "POST /webhooks/whatsapp",
    # D43 Twilio Sandbox: signed (X-Twilio-Signature) inbound and receipt webhooks, plus the
    # HMAC-signed, 15-minute quotation PDF link Twilio fetches as outbound media.
    "POST /webhooks/twilio",
    "POST /webhooks/twilio/status",
    "GET /media/quotations/{outbox_id}/{expires}/{supplied}/quotation.pdf",
    # D47 Gmail through Apps Script: signed mail push, reply claim and reply receipt.
    "POST /callbacks/google/mail/inbound",
    "POST /callbacks/google/mail/claim",
    "POST /callbacks/google/mail/receipt",
}


def operations(application) -> dict[str, bool]:
    """Map 'METHOD path' to whether the operation declares a security requirement in its OpenAPI description."""
    return {
        f"{method.upper()} {path}": bool(operation.get("security"))
        for path, methods in application.openapi()["paths"].items()
        for method, operation in methods.items()
    }


def test_staff_api_surface_is_the_reviewed_inventory_and_only_health_is_open():
    """Every staff operation is in the inventory and requires a bearer credential except the liveness check."""
    found = operations(staff)
    assert set(found) == STAFF_OPERATIONS
    assert [name for name, secured in found.items() if not secured] == ["GET /api/health"]


def test_gateway_exposes_only_signed_receivers_and_no_documentation_or_staff_route():
    """The internet-facing gateway lists no staff route, no OpenAPI/docs endpoint and exactly the signed receivers."""
    assert gateway.docs_url is None and gateway.openapi_url is None and gateway.redoc_url is None
    assert set(operations(gateway)) == GATEWAY_OPERATIONS
    assert not any("/api/" in name for name in operations(gateway))


def test_staff_api_directly_mounted_paths_are_health_and_documentation_only():
    """Beyond the routers, only liveness and FastAPI's documentation routes exist (local-only, never tunneled)."""
    documentation = {"/api/health", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
    top_level = {getattr(route, "path", None) for route in staff.router.routes if hasattr(route, "path")}
    assert top_level == documentation
