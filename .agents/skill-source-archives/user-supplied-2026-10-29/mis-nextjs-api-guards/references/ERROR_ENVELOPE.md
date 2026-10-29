# Error envelope, codes, correlation & audit

One response shape across the whole API so clients branch on a stable flag and
machine code — never on prose or HTTP status alone.

## The envelope

```jsonc
// success
{ "ok": true, "data": { /* payload */ }, "requestId": "8f3c…" }

// failure
{ "ok": false, "error": { "code": "validation_failed", "message": "…", "details": { /* optional */ } }, "requestId": "8f3c…" }
```

- `ok` — the discriminant clients switch on.
- `error.code` — a **stable** `ErrorCode` string; safe to branch on in code.
- `error.message` — human-readable, client-safe.
- `error.details` — optional structured extra (e.g. Zod's flattened issues).
- `requestId` — correlation id, mirrored on the `X-Request-Id` response header.

Build them with the responders (they take `ctx` for the id):

```ts
import { ok, fail } from "@/shared/api/respond"
return ok(ctx, order)                                   // 200
return ok(ctx, created, { status: 201 })                // custom status
return fail(ctx, 403, "forbidden", "Not your order")    // explicit failure
```

## Throwing instead of returning

Anywhere in a guard or handler you can throw a typed error; the runner renders
it. This keeps deep call stacks clean (no `Response` plumbing through services).

```ts
import { NotFoundError, ForbiddenError, ConflictError } from "@/shared/api/errors"

const order = await getOrder(id)
if (!order) throw new NotFoundError("Order not found")
if (order.locked) throw new ConflictError("Order is locked")
```

| Class | Status | Code |
|---|---|---|
| `BadRequestError` | 400 | `bad_request` |
| `ValidationError` | 400 | `validation_failed` |
| `UnauthorizedError` | 401 | `unauthorized` |
| `ForbiddenError` | 403 | `forbidden` |
| `NotFoundError` | 404 | `not_found` |
| `ConflictError` | 409 | `conflict` |
| `RateLimitedError` | 429 | `rate_limited` |
| `UpstreamError` | 502 | `upstream_error` |
| `TimeoutError` | 504 | `timeout` |
| `ApiError` (base) | any | any `ErrorCode` |

**Any non-`ApiError` throw becomes a 500 `internal_error`** with a generic
message — the original error is logged with the `requestId` but never sent to the
client, so internals don't leak.

## Full code list

`bad_request`, `validation_failed`, `unauthorized`, `forbidden`, `not_found`,
`method_not_allowed`, `unsupported_media_type`, `payload_too_large`, `conflict`,
`rate_limited`, `unavailable`, `timeout`, `upstream_error`, `internal_error`.

## Correlation id

The runner reads an inbound `X-Request-Id` (so a gateway/front-end trace flows
through) or generates a UUID. It is:

- bound to `ctx.log` (every line carries it),
- placed in the envelope `requestId`,
- stamped on the `X-Request-Id` response header on **every** path — success,
  guard short-circuit, and thrown errors.

Echo it from the client on retries to correlate logs end-to-end.

## Audit logging

Always-on: the runner emits one structured `request` line per call —
`{ method, path, status, durationMs, shortCircuited, ip, requestId }`. Add the
`audit()` guard for a business-level `audit` line that also records the `tag`
and `actorId`. Both go through the configured `Logger` (JSON by default; swap for
pino — see `ADAPTERS.md`).

## Mapping upstream failures (e.g. GAS → 502)

When a route calls a slow/fallible upstream like a Google Apps Script web app
(`mis-gas-api`), translate its failure into the envelope so clients see a clean
502 instead of a leaked stack:

```ts
import { UpstreamError } from "@/shared/api/errors"
import { timeout } from "@/shared/api/guards/timeout"

export const POST = defineRoute({
  guards: [auth(), validate({ body: PayslipSchema }), timeout(120_000)],
  handler: async function generatePayslip(_req, ctx) {
    try {
      const pdf = await callGas("generate-payslip", ctx.body)   // mis-gas-api client
      return ok(ctx, pdf)
    } catch (err) {
      ctx.log.error("gas_failed", { error: err instanceof Error ? err.message : String(err) })
      throw new UpstreamError("Payslip service is unavailable")  // → 502 upstream_error
    }
  },
})
```

`timeout(120_000)` bounds the GAS call (which can run 60–120s) and yields a 504
on overrun; the `try/catch` converts other GAS failures to a 502. Run such routes
on the Node runtime (`export const runtime = "nodejs"`), not Edge.
