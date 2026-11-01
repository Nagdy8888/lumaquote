"""Temporary tunnel composition exposing only signed Google callbacks, never staff APIs."""

from fastapi import FastAPI

from luma.core.errors import DomainError
from luma.core.http import domain_error, response_boundaries
from luma.features.google_sync.routes import router

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_exception_handler(DomainError, domain_error)
app.middleware("http")(response_boundaries)
app.include_router(router)
