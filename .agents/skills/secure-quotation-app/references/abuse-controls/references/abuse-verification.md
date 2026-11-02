# Evidence for abuse controls

Exercise observable outcomes at HTTP, job, tool, and database interfaces. Tests must include actual concurrent callers; mocking every counter/reservation operation does not prove atomicity.

- Rate boundary: permit admitted work, reject the next disallowed request, test burst/window rollover, and verify retry behavior.
- Multi-process behavior: simultaneous requests near a cap stay within it across multiple clients/workers. Restarting a process does not reset shared allowances.
- Identity: forged forwarded headers, caller-supplied company IDs, changed IPs, and alternate routes cannot choose a higher allowance. One customer's limit does not block unrelated customers without an explicit shared-cap reason.
- Reservation race: competing last-budget requests admit only the allowed work. Repeated submissions do not reserve multiple times.
- Idempotency: concurrent same-key submissions have one business effect; changed payload conflicts; another principal cannot replay private results.
- Resource bounds: large bodies, long audio, decompression expansion, parser CPU, many queued jobs, oversized model context, and endless tool loops stop at enforced boundaries.
- Outage: limiter/database unavailable prevents paid or mutating dispatch without dropping durably accepted work. Recovery preserves limits and deferred state.
- Recovery: simulate crash before/after provider submission, expired worker lease, lost response, and cancellation. Uncertain usage/send outcomes remain visible and are not blindly retried.
- Webhooks: verify signatures before parsing sensitive content, duplicate and batched events, out-of-order delivery receipts, capacity saturation, and persisted deferral.
- Approvals: expired/revised quotes, revoked staff permission, duplicate resumes, and takeover prevent unauthorized sends even while a queued job retries.
- Bypass: direct Supabase Auth, REST, RPC, and Storage paths cannot sidestep applicable protections. Use authenticated/anon roles rather than a service-role test client.
- Trace/log privacy: inject canary secrets and PII; verify they do not appear in application logs, exported LangSmith traces, metrics labels, exception messages, or test artifacts.

Record the tested policy profile, concurrency, environment, commands, and results. Distinguish local fixtures, provider sandboxes, and live enforcement. Missing coverage is Not Run, not Passed. Installing a skill proves none of these controls are implemented.

