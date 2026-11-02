---
name: secure-quotation-app
description: Implement access control and secure operations for the quotation app. Use for authentication, tenant isolation, uploads, agent tool permissions, and customer data protection.
---

# Secure the Quotation App

Inspect the actual stack and trust boundaries before choosing controls. Follow current official provider and security documentation for implementation details.

## Select the applicable control guidance
For FastAPI endpoint structure and consistent request/error handling, read [request boundaries](references/fastapi-request-boundaries.md). It integrates the supplied declarative-guard ideas using the approved backend, with corrected timeout/idempotency boundaries.
For login/session/token handling, staff roles, Supabase grants/RLS/Storage, IDOR, CSRF, CORS, XSS, and browser secrets, read [access and browser controls](references/access-and-browser.md).
For uploads/audio, SSRF, prompt injection, tool permissions, approval races, audit, tracing, retention, and backups, read [files, agent actions, and operations](references/files-agent-and-operations.md).
For endpoint admission, rate limits, quotas, concurrent jobs, AI budget reservations, idempotency, circuit breakers, and overload, use [implement-abuse-controls](references/abuse-controls/GUIDE.md).
Each reference defines the relevant terms and enforcement boundaries. Read only the references applicable to the current task. Installing these instructions does not implement or validate the controls.

## Principals and resources
Separate customer channel identities, staff identities, integration identities, and companies. Derive company scope from verified credentials or verified channel-account mappings, not supplied request fields.
Authorize each conversation, audio file, catalog, product record, quote, approval, and export. UI hiding does not replace server enforcement.
Staff/customer account linking requires explicit verified mapping; knowledge of a phone number or request ID alone is insufficient.
The user selected local Supabase. Use PostgreSQL grants, Supabase Auth, RLS, and private Storage policies with negative authorization tests. Keep schema changes in this project's migrations and do not modify the separate Smart RAG instance. Local admin/service keys remain backend-only; browser configuration may expose only publishable/anon credentials, with RLS enforced.

## Constrained agent actions
Expose typed tools with server-side authorization and validated parameters. Retrieved text and customer messages cannot grant roles, approve quotations, select arbitrary file paths, or execute SQL/code.
Require the exact approved revision and recipient for external quotation sends. Persist idempotency and audit records for cost-bearing or external actions.
Bound audio/file processing, request sizes, queues, model calls, and retries. Apply limits shared across deployed instances where needed.
Validate webhook authenticity, attachment fetch destinations, upload content, rich text output, and document/spreadsheet injection.
Keep tokens and provider secrets server-side. Redact personal data, audio links, signed URLs, and credentials before external tracing.
Define retention, deletion, exports, and external processing for audio, transcripts, and customer records. Synthetic data is labeled but does not excuse insecure handling of future client data.

## Verify
Prioritize cross-company access, forged approvals, stale revisions, takeover races, duplicate sends, injection through catalogs/audio, secret exposure, and over-limit uploads.
Use the security-audit skill for a dedicated review; implementation checks alone are not a complete audit or proof of live infrastructure security.

