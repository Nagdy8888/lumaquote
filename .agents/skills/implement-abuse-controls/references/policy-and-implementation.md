# Admission policy for the quotation workflow

## Identity and scope
Use server-derived company, user/customer, operation class, and resource identity. IP admission is supplementary and must use trusted proxy configuration; arbitrary X-Forwarded-For values cannot choose limiter keys. Combine user/company limits with a global capacity boundary and bounded key cardinality/retention.
For WhatsApp, authenticate provider origin, map the receiving account to the company, and apply customer limits using the sender identifier from the verified event. Do not throttle every customer as one person merely because Meta uses shared delivery IPs.

Separate cheap reads, quotation edits, approvals/sends, model runs, audio duration/bytes, uploads, exports, login/recovery, and webhook ingestion. Reads cannot borrow an expensive operation's permissions.
Supabase browser-direct Auth/REST/Storage requests bypass FastAPI middleware. Configure Auth's own limits and database/storage permissions. Business transitions and expensive tools must not remain callable through a less-protected RPC or direct table write.

## Rate, quota, and concurrent execution
Choose an algorithm with explicit burst/window semantics and clock assumptions. Atomic conditional updates or locked transactions must cover concurrent API instances and workers. Counter read-then-write in separate transactions is insufficient.
Give counters bounded retention. A transaction's database timestamp can coordinate a window; an application clock must not let clients choose/reset it.
Acquire leased concurrency slots before dispatch. Heartbeat long work, detect expiry, and prevent expired/stale owners from completing business transitions with fencing/version checks.
Use finite queue capacity and per-company fairness. Separate customer latency from bulk catalog ingestion. A worker lease prevents ownership conflicts; it does not prove an external provider call happened only once.

## Spending and usage
Bound input/context size, output tokens, model/tool calls, iterations, audio duration, ingestion volume, and retries per run. A model cannot select an arbitrary more expensive model or increase its own limits.
Reserve a conservative estimated maximum against relevant company/user/global configured allowances in one atomic admission step, then give child work the run-local allowance. Account for retries and provider-hidden/internal calls where applicable.
Use Decimal or integer currency subunits, explicit currency/rate/model versions, and documented period/timezone boundaries. A reservation must not vanish at a period boundary while its job is still running.
Reconcile completed calls from observed usage. A timeout may mean a provider accepted work; keep unresolved consumption marked uncertain until reconciled instead of immediately freeing it for retries. Crash recovery must consider in-flight provider calls.
Define reservation expiry, heartbeat, completion, cancellation, and stale-job cleanup. Cancellation is not proof that a provider stopped charging.
Label token-price amounts as estimates; provider charges, delayed usage reporting, and price changes can differ. Provider budget dashboards may not enforce a real-time hard cap. Do not promise zero overspend from estimated accounting alone.

## Idempotency and backpressure
Scope idempotency to company/principal/action and bind the key to a canonical payload fingerprint. Same key plus changed content is a conflict. Concurrent identical submissions resolve to one operation; result replay still checks current authorization.
Separate inbound event identity, agent run, quote revision, and outbound action identity. For status events, do not deduplicate every later status by message ID alone.
For a verified webhook, acknowledge only after durable acceptance, including an intentional recorded no-op for duplicates. If durable acceptance fails, do not return success and drop the event. Do not retry accepted events simply because later customer processing is throttled; record its deferred/limited state.
Decide bounded webhook overload and poison-event handling according to Meta's current documented retry behavior. Keep retry storms from amplifying calls.
Ordinary callers may receive 429 with a meaningful Retry-After for a timed limit, 413 for oversized input, or a sanitized 503 when enforcement is unavailable. A staff approval that cannot be recorded remains unapproved.
Use exponential backoff with jitter and finite attempts only for eligible transient failures. Reconcile unknown outbound delivery before retry. Recheck ownership and quote approval at actual send time.

## Public portfolio access
If an anonymous playground is implemented, isolate synthetic sessions from staff data and live messaging. Limit session lifetime, simultaneous runs, transcript length, audio duration, uploads, and per-session/global consumption. An anonymous visitor cannot approve a company quotation or trigger a real customer send.

