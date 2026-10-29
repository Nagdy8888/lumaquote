# Security notes

Rules the guards encode, and the reasoning. Treat these as non-negotiable in
production reviews.

## 1. Principal from the verified session only — never a header

The `AuthAdapter` derives the principal from a cryptographically verified session
(`supabase.auth.getUser()` re-validates the JWT against the auth server). Never
trust `X-Auth-User`, `X-User-Id`, or any client-supplied identity header — they
are trivially spoofed. The old `with-auth.ts` already enforced this; the standard
keeps it. Do not add a guard or handler that reads identity from a header.

## 2. No mass-assignment

`validate({ body: Schema })` passes **only the schema's fields** to the handler
(`ctx.body`). A client cannot smuggle `{ isAdmin: true, ownerId: "…" }` into a
create/update by adding extra keys — they're dropped. Never spread raw
`req.json()` into a database write; write through `ctx.body`.

## 3. CSRF on cookie-authenticated mutations

Cookies are sent automatically cross-site, so cookie-auth mutations need a CSRF
defense. Add `origin()` to state-changing routes — it rejects POST/PUT/PATCH/
DELETE whose `Origin` isn't your host (or your allowlist). Token auth
(`Authorization: Bearer`) isn't auto-sent and is less exposed, but `origin()` is
cheap defense-in-depth. `cors()` with an explicit `origins` allowlist (not `*`
when `credentials: true`) controls who can read responses cross-origin.

## 4. Rate-limit ordering

Put `rateLimit()` **before** `auth()` so unauthenticated floods are rejected
before the (more expensive) session verification and DB lookups. For per-user
quotas, add a **second** `rateLimit({ keyBy: "principal" })` after `auth()`. Use
the **distributed** adapter (Upstash) in production — `inMemoryRateLimit` is
per-isolate and gives attackers `limit × instances` on serverless.

## 5. Idempotency prevents double-effects

For mutations that must not run twice on retry (payments, sending email, creating
records), require an `Idempotency-Key` and add `idempotency()`. A retried key
replays the stored result; an in-flight key returns 409. Only successful (`<300`)
responses are stored, so a failed attempt can be retried.

## 6. Fail closed, leak nothing

- Unknown thrown errors → generic 500 `internal_error`; the real error is logged
  with the `requestId`, never sent to the client.
- Guards reject with the **narrowest informative** status: 401 (no session), 403
  (no permission), 404 (ownership miss — don't reveal existence to non-owners),
  429 (throttled).
- `ownership()` returns 404 before 403 when the resource doesn't exist, so you
  don't disclose which ids are valid to a probing caller.

## 7. Timeouts and resource bounds

`timeout(ms)` bounds slow handlers/upstreams (→ 504) so a hung dependency can't
pin a serverless function for its full platform limit. `bodyLimit(bytes)` and
`contentType()` reject oversized or wrong-typed payloads early.

## 8. Correlation for incident response

Every response carries `X-Request-Id` and every log line is bound to it. When
triaging, ask the client for the id from the failed response and grep logs — the
full guard/handler trail is keyed by it.

## Review red flags

- Identity read from a request header instead of `ctx.principal`.
- Raw `req.json()` spread into a write (mass-assignment).
- A mutation route with no `validate({ body })` and no `origin()`.
- `inMemoryRateLimit` reachable in production config.
- Hand-built `NextResponse.json({ error })` that bypasses the envelope (clients
  may come to depend on an inconsistent shape).
- `roles`/`permissions`/`ownership` without `auth()` before them (runtime failure
  today — ordering isn't yet compile-enforced; see `GUARD_PIPELINE.md`).
