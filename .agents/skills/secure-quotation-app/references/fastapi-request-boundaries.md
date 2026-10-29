# FastAPI request boundaries

The supplied declarative route-guard concept is adapted to FastAPI dependencies, middleware, and explicit service checks. Keep one business backend. No TypeScript route-runner or hosted rate-limit service is installed from the supplied templates.

## Request sequence
Use cheap method/content/size and coarse admission checks before expensive work. Verify identity, derive company scope, validate typed input, and check action/object/property permissions before business effects.
After identity, apply user/company admission, payload-scoped idempotency, and budget/concurrency reservation at the actual operation boundary. Reauthorize result replay and downstream dispatch.
Use FastAPI/Pydantic contracts and an explicit typed principal. Never derive staff authority from arbitrary identity headers, caller company fields, or raw unvalidated JSON.
Keep role, ownership, rate, and input decisions observable in tests. Do not assume a dependency list alone proves every execution path is protected.

## Consistency and failures
Use one documented response/error shape with stable safe error codes and correlation IDs. Treat incoming request IDs as untrusted; validate or replace them, and never allow them to inject log lines.
Log denied and failed attempts without leaking input, credentials, raw SQL, or stack traces to clients. Avoid resource-existence disclosures according to the endpoint contract.
Handle CORS/CSRF for the actual browser authentication transport; CORS does not protect non-browser calls.
A timeout response does not prove a coroutine, parser, provider call, or external send stopped. Use enforced deadlines, cancellation-aware adapters, and uncertain-outcome reconciliation.
Scope idempotency to company/principal/action and payload fingerprint. A response cache keyed only by URL and user-supplied key is insufficient; storing only successes cannot by itself make external retries safe.
A local in-memory counter does not enforce a shared deployment limit. Use the selected atomic PostgreSQL implementation when suitable, with explicit outage behavior.

Use implement-abuse-controls for admission/recovery detail, secure-quotation-app for trust boundaries, and the official FastAPI skill for current dependency/streaming APIs. Test direct Supabase access paths alongside FastAPI.

