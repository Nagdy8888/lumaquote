# Adapters — pluggable backends

Routes never name a backend. Guards read whichever adapter you wire once via
`configureGuards(...)`. Swap providers without touching a single route.

## The four contracts

```ts
interface AuthAdapter        { getPrincipal(req): Promise<Principal | null> }
interface RateLimitAdapter   { hit(key, limit, windowMs): Promise<RateLimitResult> }
interface IdempotencyAdapter { reserve(key, ttlMs): Promise<IdempotencyReservation> }
interface Logger             { debug/info/warn/error(msg, fields?); child(bindings): Logger }
```

`configureGuards` takes any subset; a guard that needs an unconfigured adapter
throws a clear boot-time error naming the fix. `logger` defaults to
`consoleLogger()`.

## Wiring (once, at boot)

Copy `assets/template-bootstrap.ts` → `shared/api/bootstrap.ts`, then run it
before any route. The reliable hook is `instrumentation.ts`:

```ts
// instrumentation.ts (project root or src/)
export async function register() {
  await import("@/shared/api/bootstrap")
}
```

## Default adapters

| Adapter | Default impl | Runtime | Requires |
|---|---|---|---|
| Auth | `supabaseAuth({ mapUser })` | Node + Edge | `@supabase/ssr`, `@supabase/supabase-js` |
| Rate limit | `upstashRateLimit()` | Node + Edge | `@upstash/redis` |
| Rate limit (dev) | `inMemoryRateLimit()` | any (per-process) | — |
| Idempotency | `upstashIdempotency()` | Node + Edge | `@upstash/redis` |
| Logger | `consoleLogger()` | any | — |

### `supabaseAuth`

Verifies the session with `supabase.auth.getUser()` — which re-validates the JWT
against the auth server, unlike the spoofable `getSession()`. You provide
`mapUser(user) => Principal` to attach roles/permissions **from your database**
(Supabase doesn't own your RBAC model):

```ts
supabaseAuth({
  async mapUser(user) {
    const profile = await getProfile(user.id)
    return { id: user.id, email: user.email, roles: profile.roles, permissions: profile.perms }
  },
})
```

### `upstashRateLimit` / `upstashIdempotency`

Use Upstash Redis over its REST API — so they run on the **Edge runtime** and,
crucially, share state across serverless isolates. `upstashRateLimit` is a
fixed-window counter (`INCR` + `PEXPIRE`). Pass a pre-built `Redis` client or let
it read `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN`.

### `inMemoryRateLimit` — dev/test only

A process-local `Map`. **Not distributed**: each isolate keeps its own counters,
so on Vercel the effective limit is `limit × instances`. Use only locally and in
unit tests; the bootstrap template switches on `NODE_ENV`.

## Edge vs Node

- All defaults are **Edge-safe** (Upstash is fetch-based; `@supabase/ssr` runs on
  Edge). `consoleLogger` and `inMemoryRateLimit` are pure JS.
- The runner uses `crypto.randomUUID()` and `performance.now()` — both present in
  the Edge runtime and Node ≥ 18.
- Long upstream calls (e.g. Google Apps Script, 60–120s) should run on the **Node
  runtime** (`export const runtime = "nodejs"`), not Edge — pair them with
  `timeout()`. See `mis-gas-api` → `CALLING_FROM_NEXTJS.md`.

## Writing a custom adapter

Implement the interface and pass it to `configureGuards`. Examples:

```ts
// Clerk auth
const clerkAuth: AuthAdapter = {
  async getPrincipal() {
    const { userId, sessionClaims } = await auth()  // @clerk/nextjs/server
    if (!userId) return null
    return { id: userId, roles: (sessionClaims?.roles as string[]) ?? [] }
  },
}

// Sliding-window limiter via @upstash/ratelimit (wrap to our per-call signature)
const slidingLimit: RateLimitAdapter = {
  async hit(key, limit, windowMs) {
    const rl = new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(limit, `${windowMs} ms`) })
    const r = await rl.limit(key)
    return { success: r.success, limit: r.limit, remaining: r.remaining, reset: r.reset }
  },
}

configureGuards({ auth: clerkAuth, rateLimit: slidingLimit })
```

A custom logger just needs the five methods; back it with pino:

```ts
const pinoLogger = (base = pino()): Logger => ({
  debug: (m, f) => base.debug(f, m),
  info:  (m, f) => base.info(f, m),
  warn:  (m, f) => base.warn(f, m),
  error: (m, f) => base.error(f, m),
  child: (b) => pinoLogger(base.child(b)),
})
```
