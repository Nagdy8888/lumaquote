"""Temporary tunnel composition exposing only signed Google callbacks and verified WhatsApp ingress, never staff APIs.

Routes: signed Google callbacks, the Meta webhook (`/webhooks/whatsapp`), the Twilio webhooks
(`/webhooks/twilio`, `/webhooks/twilio/status`) and the HMAC-signed, expiring quotation PDF
link Twilio fetches (`/media/quotations/...`), and the signed Apps Script Gmail endpoints
(`/callbacks/google/mail/inbound|claim|receipt`, D47). Each route refuses work unless configured.
"""

from fastapi import FastAPI

from luma.core.errors import DomainError
from luma.core.http import domain_error, response_boundaries
from luma.features.google_sync.routes import router
from luma.features.messaging.email_routes import router as email_router
from luma.features.messaging.media_links import router as media_link_router
from luma.features.messaging.twilio_webhook import router as twilio_router
from luma.features.messaging.webhook import router as whatsapp_router

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_exception_handler(DomainError, domain_error)
app.middleware("http")(response_boundaries)
app.include_router(router)
app.include_router(whatsapp_router)
app.include_router(twilio_router)
app.include_router(media_link_router)
app.include_router(email_router)
