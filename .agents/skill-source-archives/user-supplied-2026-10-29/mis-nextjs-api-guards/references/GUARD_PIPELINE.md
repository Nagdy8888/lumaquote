# The guard pipeline — contract & type fold

How `defineRoute`, `Guard`, and `GuardContext` fit together, and the TypeScript
that makes the context type itself up as guards run.

## The three pieces

### `GuardContext` — the per-request bag

Built once by the runner, then mutated as guards add to it. Rough equivalent of
NestJS's `ExecutionContext`.

```ts
interface GuardContext {
  readonly req: NextRequest
  readonly requestId: string          // correlation id, on every log line + X-Request-Id
  readonly ip: string | null
  params: Record<string, string>      // awaited from Next 15's promise once, by the runner
  readonly log: Logger                // pre-bound to requestId
  readonly startedAt: number
  readonly responseHeaders: Headers   // guards stage headers here; runner merges them
  readonly onResponse: (hook: (res: Response) => void | Promise<void>) => void
  readonly state: Record<string, unknown>
}
```

Two interceptor primitives matter:

- **`responseHeaders`** — `cors()` and `rateLimit()` stage headers here; the
  runner copies them onto the final response (success *or* short-circuit), so a
  guard never needs to touch the eventual response object.
- **`onResponse(hook)`** — register a post-response interceptor. `idempotency()`
  uses it to persist the successful response after the handler returns.

### `Guard<Needs, Adds>` — a unit of protection

```ts
interface Guard<Needs extends object = object, Adds extends object = object> {
  readonly name: string
  run(ctx: GuardContext & Needs): GuardOutcome<Adds> | Promise<GuardOutcome<Adds>>
  readonly __types?: { needs: Needs; adds: Adds }   // phantom — types only
}
type GuardOutcome<Adds extends object> = void | undefined | Adds | Response
```

`run` returns:

- `undefined` / `void` → **pass**, contribute nothing;
- an **object** → pass, the object is merged into the context (its `Adds`);
- a **`Response`** → **short-circuit**; the runner returns it (after merging
  `responseHeaders` and stamping the correlation id).

`Needs` documents what an earlier guard must have added (e.g. `roles()` needs
`{ principal }`). `Adds` is what this guard contributes downstream.

> **Why `run` is a method, not an arrow property.** Method parameters are
> checked *bivariantly* in TypeScript. That lets a guard that requires
> `{ principal }` still be assignable to the base `Guard` type the route tuple
> uses. An arrow property (`run: (ctx) => …`) is contravariant under
> `strictFunctionTypes` and would reject such guards from the array. Keep it a
> method.

### `defineRoute` — the runner entry point

```ts
export const POST = defineRoute({
  guards: [auth(), roles("admin"), validate({ body: Schema })],
  handler: async (req, ctx) => ok(ctx, /* ctx.principal, ctx.body are typed */),
})
```

`defineRoute` returns a function with the **exact signature Next.js calls**
(`(req, ctx) => Promise<Response>`), so `export const POST = defineRoute(...)`
just works. Internally it builds the context, runs the chain, and finalizes.

## The type fold — how `ctx` types itself

The job: given `guards: [auth(), validate({ body })]`, infer
`ctx.principal: Principal` and `ctx.body: { … }` for the handler — in one pass,
without manual annotations.

```ts
type AddsOf<G> = G extends { __types?: { adds: infer A } } ? NonNullable<A> : object

type AccumulateAdds<G extends readonly unknown[]> =
  G extends readonly [infer Head, ...infer Tail]
    ? AddsOf<Head> & AccumulateAdds<Tail>
    : object

type RouteContextFor<G extends readonly Guard[]> = GuardContext & AccumulateAdds<G>
```

- Each guard carries its `Adds` in the `__types` phantom (never constructed at
  runtime). `AddsOf` reads it back out.
- `AccumulateAdds` walks the tuple and **intersects** every `Adds`.
- `defineRoute<const G extends readonly Guard[]>` uses the **`const` type
  parameter** so the array literal keeps its precise tuple type (each element's
  `Adds` preserved) instead of widening to `Guard[]`.

The handler param is `GuardContext & AccumulateAdds<G>` — so `auth()`'s
`{ principal }` and `validate()`'s `{ body }` are both present and typed.

This is why the array style beats HOF chaining: inference happens **once over a
flat tuple** rather than threading accumulated generics through N nested calls
(where TS routinely gives up and widens `ctx` to `{}`). See
`CONVENTION_COMPARISON.md`.

## The runner's responsibilities (in order)

1. Read/generate `requestId`; resolve `ip`; **await `ctx.params`** once; bind the logger.
2. Run guards in array order: merge object outcomes, short-circuit on a `Response`.
3. If a guard **throws**, catch centrally → envelope (ApiError → its status; else 500).
4. Otherwise call the handler. If `timeout()` set a budget, race it (overrun → 504).
5. **Finalize**: merge `ctx.responseHeaders`, stamp `X-Request-Id`.
6. Run `onResponse` hooks (idempotency persistence, extra audit).
7. Emit the always-on `request` audit line (method, path, status, latency).

Steps 3, 5, 6, 7 are why guards/handlers never build envelopes or set the
correlation header themselves — the runner guarantees it on every exit path.

## Escape hatches

- **`compose(...guards)(handler)`** — same runner, HOF shape, for teams that
  prefer function composition. `compose(auth(), roles("admin"))(h)` ≡
  `defineRoute({ guards: [auth(), roles("admin")], handler: h })`.
- **Plain handler** — nothing forces `defineRoute`. A trivial endpoint can still
  be `export async function GET() { … }`. You lose the envelope/correlation/audit.

## Writing a custom guard

```ts
import { fail } from "@/shared/api/respond"
import type { Guard } from "@/shared/api/types"

/** Require a non-empty `X-Tenant` header and expose it as ctx.tenantId. */
export function tenant(): Guard<object, { tenantId: string }> {
  return {
    name: "tenant",
    run(ctx) {
      const id = ctx.req.headers.get("x-tenant")
      if (!id) return fail(ctx, 400, "bad_request", "Missing X-Tenant header")
      return { tenantId: id }   // becomes ctx.tenantId, typed, downstream
    },
  }
}
```

Unit-test it in isolation by calling `tenant().run(fakeCtx)` — no HTTP needed
(see `assets/template-route-handler.test.ts`).

## Known limitation (v1.0)

The fold infers `Adds` but does **not yet enforce `Needs` ordering** at compile
time — putting `roles()` before `auth()` is not a type error today (it fails at
runtime when `ctx.principal` is undefined). Ordering enforcement via the
`Needs` phantom is planned for v1.1. Until then, follow the canonical order.
