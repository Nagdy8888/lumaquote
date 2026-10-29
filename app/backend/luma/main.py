from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from luma.core.errors import DomainError
from luma.core.http import domain_error, response_boundaries
from luma.features.catalog.routes import router as catalog
from luma.features.conversations.routes import router as conversations
from luma.features.quotations.routes import router as quotations
from luma.features.workspace.routes import router as workspace

app = FastAPI(title="LumaQuote API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
app.add_exception_handler(DomainError, domain_error)
app.middleware("http")(response_boundaries)
for router in (conversations, quotations, catalog, workspace):
    app.include_router(router)


@app.get("/api/health")
def health():
    """Return process health only; this does not establish database or external-provider readiness."""
    return {"status": "ok", "service": "lumaquote", "version": "0.1.0"}
