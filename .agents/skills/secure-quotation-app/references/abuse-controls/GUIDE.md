---
name: implement-abuse-controls
description: Implement rate limiting, request quotas, AI spending reservations, concurrency limits, and backpressure for the FastAPI, LangGraph, Supabase, and WhatsApp quotation workflow. Use for endpoint admission, expensive jobs, public playground abuse, and failure recovery.
---

# Implement Abuse Controls

Protect staff APIs, customer messages, uploads/audio, background jobs, model calls, and outbound actions. This skill defines implementation guidance, not an already enforced security feature.

## Terms that must remain distinct
- Rate limit: how frequently an operation may start, including any allowed burst.
- Quota: total allowed consumption within a specified period.
- Concurrency limit: how much work may be in progress at once.
- Budget reservation: atomic allocation of estimated maximum consumption before expensive work.
- Backpressure: bounded admission or deferral when downstream capacity is exhausted.
- Idempotency: repeat submission does not create repeat business effects.
- Circuit breaker: temporarily stop calls to an unhealthy dependency; it is not a rate limiter.
- Tenant isolation: one company's work, data, or exhausted allowance cannot grant access to another company's resources.

## Workflow
Read the actual endpoint/tool contracts and [policy and implementation](references/policy-and-implementation.md) before implementing controls. Use [abuse verification](references/abuse-verification.md) when adding tests or claiming enforcement.
For each operation, specify the authenticated principal/scope, limiter keys, rate/window/burst, cost units, concurrency, maximum queued work, reservation, deadline, retry ceiling, denial behavior, and cleanup.
Keep limits in typed configuration with an explicitly named local/public/production profile. Choose concrete values using provider limits, available resources, expected use, and a bounded load test. No value is an industry-wide safe default.
For a new paid/public operation, do not leave admission or cost bounds undefined. Resolve consequential missing spend decisions with the user; continue independent implementation and local tests without authorizing external spending.
The API and worker must enforce the same policy. A UI cooldown, prompt instruction, or in-memory semaphore in one process does not enforce a deployment-wide limit.
Do not add Redis or another paid dependency automatically. PostgreSQL is already selected and may provide atomic counters, reservations, and leases when it meets latency/load requirements.
Use [secure-quotation-app](../../SKILL.md) for identity, browser, upload, tool permission, and data boundaries.

## Required behavior
- Perform cheap structural/size checks and coarse admission before costly parsing/auth-key fetches; then use verified identity for company/user/action limits.
- Atomically admit work, reserve relevant quota/budget, and create or resolve its idempotent job before any model/transcription call or send.
- Reject unauthorized calls regardless of available quota. Idempotency never bypasses authorization.
- Do not grant unlimited execution during limiter/database outages. Deny or durably defer expensive/mutating work, distinguishing temporary inability to enforce from exhausted allowance.
- Return useful bounded retry information without leaking customer identities, budget balances, or internal infrastructure.
- Keep external invoices separate from accounting estimates. A model usage ledger cannot prove the provider's billed total.

## Source guidance
Verify current provider behavior during implementation:
- [OWASP REST security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
- [OWASP denial of service](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html)
- [Supabase Auth rate limits](https://supabase.com/docs/guides/auth/rate-limits)

