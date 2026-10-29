---
name: integrate-whatsapp
description: Implement WhatsApp Business Platform messaging, media intake, delivery events, and recovery for the quotation app. Use for channel adapters and webhook behavior.
---

# Integrate WhatsApp

Inspect the chosen provider and verify its current official webhook, authentication, media, template, consent, pricing, and messaging-window documentation. Do not encode remembered policy or quota values as permanent facts.

## Portfolio integration choice
Use Meta's WhatsApp Cloud API directly with its developer test number and authorized test recipients for development and the recorded portfolio walkthrough.
The user requested free WhatsApp integration. Do not introduce a paid messaging provider, subscription, paid template sends, or production billing as a default.
Confirm current test-account restrictions during setup. Free WhatsApp testing does not establish that model inference, transcription, hosting, or unrestricted production messaging is free.
Use [whatsapp-webhooks](../whatsapp-webhooks/SKILL.md) for Meta's verification handshake, raw-body signature validation, and inbound/status payload examples.
Its examples are starting points: retain this project's durable queue, tenant isolation, approval, deduplication, and takeover requirements.
Before adapting examples, reject missing/empty webhook secrets at startup, replace customer-content console logging with redacted operational events, and persist accepted events before acknowledging them.
Inbound message deduplication can use the message identity; delivery receipts need a distinct event identity or message-plus-status identity so an earlier receipt does not suppress a later delivered/read update. Enforce monotonic delivery transitions with the provider's actual event semantics.
Hookdeck CLI tunneling is optional; the imported skill does not require adopting Hookdeck's hosted gateway or purchasing a plan. Verify any tunnel's current free limits before choosing it.
Audio webhook intake does not itself transcribe audio; apply [process-voice-notes](../process-voice-notes/SKILL.md) for that workflow.

## Receive reliably
Verify webhook challenges and signatures using the provider's documented procedure over the correct raw bytes. Resolve the receiving business account server-side and map it to an authorized company.
Persist a validated inbound event before acknowledging it; process asynchronously. Deduplicate using company, provider account, and provider event/message identity.
Handle retries, delayed events, duplicate delivery receipts, unsupported attachments, and message edits where supported. A provider receipt must not regress a later known delivery state.
Fetch media through a restricted provider adapter with validated host/redirect behavior, credentials kept server-side, time/size limits, and authorization. Do not pass arbitrary attachment URLs to general download tools.

## Send safely
Persist outbound intent and its business action identity. Check current conversation ownership, recipient, permission, applicable policy window, approved content, and quotation revision immediately before dispatch.
Use documented idempotency when available. A timeout after submission is an unknown delivery outcome: reconcile against provider evidence; do not blindly send again.
Human takeover prevents queued automated replies from being dispatched. Serialize or otherwise coordinate dispatch with ownership changes; document the boundary for a message already accepted by the provider.
Record accepted, delivered, read where available, and failed separately. Do not equate an HTTP success with customer delivery.
Store only necessary customer data and redact credentials and media access links from logs.

## Verify
Use local fixtures or provider test facilities for signatures, duplicates, out-of-order receipts, expired media, uncertain send outcomes, human takeover races, and template/window restrictions.
Report test-mode evidence separately from live delivery. Real messages require authorization for the intended recipients and content.

