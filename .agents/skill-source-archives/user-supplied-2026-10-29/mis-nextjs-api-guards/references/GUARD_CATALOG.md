# Guard catalog

Every shipped guard: import path, signature, what it adds to the context, the
failure status/code, and notes. All live under `@/shared/api/guards/`.

Canonical order (cheap → expensive):
`method → contentType → bodyLimit → cors → origin → maintenance/featureFlag → rateLimit → auth → roles/permissions/ownership → idempotency → validate → handler`.

| Guard | Fail → code | Adds to ctx | Adapter |
|---|---|---|---|
| `method(...verbs)` | 405 `method_not_allowed` | — | — |
| `contentType(...types)` | 415 `unsupported_media_type` | — | — |
| `bodyLimit(bytes)` | 413 `payload_too_large` | — | — |
| `cors(opts)` | 204 (preflight) | — | — |
| `origin(allowed?)` | 403 `forbidden` | — | — |
| `maintenance(fn, opts?)` | 503 `unavailable` | — | — |
| `featureFlag(fn, opts?)` | 503 `unavailable` | — | — |
| `rateLimit(opts)` | 429 `rate_limited` | — | RateLimit |
| `auth()` | 401 `unauthorized` | `{ principal }` | Auth |
| `optionalAuth()` | — | `{ principal: Principal \| null }` | Auth |
| `roles(...names)` | 403 `forbidden` | — | (principal) |
| `permissions(...keys)` | 403 `forbidden` | — | (principal) |
| `ownership(load)` | 404 then 403 | `{ resource }` | (principal) |
| `idempotency(opts?)` | 409 `conflict` / replay | — | Idempotency |
| `timeout(ms)` | 504 `timeout` | — | — |
| `validate(schemas)` | 400 `validation_failed` | `{ body, query, params }` | — |
| `audit(opts?)` | — (never fails) | — | Logger |

## HTTP hygiene — `guards/http.ts`

```ts
method("GET", "POST")          // 405 + `Allow` header otherwise
contentType("application/json")// 415 on body-carrying methods with wrong type (default JSON)
bodyLimit(1_000_000)           // 413 when Content-Length exceeds the cap (header check)
```

`bodyLimit` only inspects `Content-Length` — cheap, but chunked uploads without
that header slip through; rely on the platform's hard cap as a backstop.

## CORS & CSRF — `guards/cors.ts`

```ts
cors({ origins: ["https://app.example.com"], credentials: true, maxAge: 86400 })
origin(["https://app.example.com"])  // CSRF: reject mutations from other origins
```

`cors()` answers `OPTIONS` preflights with 204 and stages `Access-Control-*`
headers onto every response via `ctx.responseHeaders`. With `credentials: true`
it echoes the request origin (never `*`). `origin()` only checks state-changing
methods; with no allowlist it requires same-origin (Origin host == Host).

## Availability gates — `guards/gate.ts`

```ts
maintenance((ctx) => flags.maintenanceOn, { retryAfterSeconds: 120 })
featureFlag((ctx) => flags.isEnabled("new-checkout"), { message: "Coming soon" })
```

Both take a predicate (sync or async) so you wire your own flag source — no
adapter. Closed → 503.

## Rate limiting — `guards/rate-limit.ts`

```ts
rateLimit({ window: "1m", limit: 10 })                          // by IP
rateLimit({ window: "1h", limit: 1000, keyBy: "principal" })    // by user (after auth)
rateLimit({ window: "10s", limit: 3, keyBy: (ctx) => apiKey(ctx), prefix: "search" })
```

`window`: ms number or `"30s"`/`"1m"`/`"1h"`/`"1d"`. Adds `X-RateLimit-Limit`,
`-Remaining`, `-Reset`; on 429 also `Retry-After`. `keyBy: "principal"` throws if
`auth()` didn't run first. Default bucket prefix is the request pathname; set
`prefix` to share/separate buckets across routes.

## Auth & authorization — `guards/auth.ts`, `guards/authorize.ts`

```ts
auth()                          // 401 if no verified session; adds ctx.principal
optionalAuth()                  // never rejects; ctx.principal may be null
roles("admin", "manager")       // 403 unless principal has a role (ADMIN always passes)
permissions("orders:write")     // 403 unless principal holds ALL listed permissions
ownership(async (ctx) => {      // 404 if null; 403 if not owner (ADMIN bypasses)
  const o = await getOrder(ctx.params.id)
  return o ? { ownerId: o.userId, resource: o } : null
})                              // adds ctx.resource (typed) on success
```

`roles()` with no args = admin-only. `permissions()` models DRF
`permission_classes` granularity, independent of roles. `isAdmin(principal)` is
exported for custom checks.

## Idempotency — `guards/idempotency.ts`

```ts
idempotency()                                   // POST/PUT/PATCH/DELETE, 24h TTL
idempotency({ header: "x-idem-key", ttlMs: 3_600_000, methods: ["POST"] })
```

Requests without the key header pass through. A known key **replays** the stored
2xx response; a key still in flight returns **409**; a new key registers an
`onResponse` hook that persists the successful response. Only `status < 300` is
stored. Requires an `IdempotencyAdapter`.

## Timeout — `guards/timeout.ts`

```ts
timeout(120_000)   // bound the handler; overrun → 504. Good in front of slow upstreams (GAS).
```

Records a budget that the **runner** enforces by racing the handler (a guard
can't wrap the handler it precedes). Bounds the handler and any guards after it,
not earlier guards.

## Audit — `guards/audit.ts`

```ts
audit({ tag: "orders.update" })   // place after auth() so actorId is populated
```

The runner already emits a baseline `request` log for every call. `audit()` adds
a business-level `audit` entry (tag, method, path, status, actorId) once the
response is known.

## Validation — `guards/validate.ts`

```ts
validate({
  params: z.object({ id: z.string().uuid() }),
  query: z.object({ page: z.coerce.number().default(1) }),
  body: z.object({ title: z.string().min(1) }),
})
```

Parses only the surfaces you pass; adds `ctx.params` / `ctx.query` / `ctx.body`,
each typed from its schema. Only schema fields survive (no mass-assignment).
Failure → 400 with `error.details = ZodError.flatten()`. `validate({ body })`
consumes the request stream — use `ctx.body`, never a second `req.json()`.
