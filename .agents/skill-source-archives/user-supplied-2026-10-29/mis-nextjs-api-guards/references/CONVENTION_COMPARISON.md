# ADR: declarative guard pipeline over HOF wrappers

**Status:** Accepted · **Supersedes:** the ad-hoc `with-auth.ts` HOF approach
(and the project ADR-0007 it referenced) · **Decision:** Convention B.

## Context

We need one standard for protecting Next.js App Router API routes across large,
production projects, legible to engineers arriving from NestJS and Django. Two
conventions were considered.

**Convention A — Composable HOF wrappers** (the prior attempt):

```ts
export const POST = withAuth(withRole("admin")(withValidation(schema)(handler)))
```

**Convention B — Declarative guard pipeline** (chosen):

```ts
export const POST = defineRoute({
  guards: [auth(), roles("admin"), validate({ body: schema })],
  handler: async (req, ctx) => ok(ctx, await create(ctx.principal.id, ctx.body)),
})
```

## The deciding factor: type inference at depth

In Convention A each wrapper changes the **handler signature it accepts**, so
accumulated context is encoded positionally. A correctly-typed generic stack
must thread the growing context through every layer:

```ts
function withAuth<C>(h: Handler<C & { principal: Principal }>): Handler<C>
function withValidation<T>(s: ZodType<T>): <C>(h: Handler<C & { body: T }>) => Handler<C>

// types must flow right-to-left through 4 nested generic instantiations:
withAuth(withRole("admin")(withValidation(schema)(async (req, ctx) => {
  ctx.principal // inferred only if EVERY layer's generics resolved
  ctx.body      // …in practice TS widens ctx to {} past ~3 layers
})))
```

With 4+ wrappers, TypeScript routinely fails to resolve the intersection and you
fall back to annotating the leaf handler by hand — defeating the purpose. You
also read execution order **inside-out and right-to-left**.

Convention B folds a **flat tuple** once (`AccumulateAdds`, see
`GUARD_PIPELINE.md`). Inference is robust because it never nests: `ctx.principal`
and `ctx.body` resolve in a single pass. We verified this with a `tsc` type test
(`assets/guards-types.test-d.ts`) that pins the inference and the negative cases.

## Scorecard

| Dimension | A — HOF wrappers | B — Declarative pipeline | Winner |
|---|---|---|---|
| Type inference at depth (4+ concerns) | Fragile; manual leaf annotations | One flat fold; inferred | **B** |
| `ctx.principal` non-null / `ctx.body` typed | Positional, brittle | Phantom `Adds` fold | **B** |
| Reading order vs execution order | Inside-out, right-to-left | Top-to-bottom = run order | **B** |
| "What protects this route?" | Unwrap the nesting | One `guards: []` array | **B** |
| Per-route config (different limits) | Wrapper args | Guard factory options | Tie |
| Unit-testing one guard | Needs a handler to wrap | `guard.run(ctx)` directly | **B** |
| Error-handling consistency | Each wrapper calls `fail()` | Runner owns the envelope | **B** |
| NestJS/DRF familiarity | Unusual | `guards: []` ≈ `@UseGuards` | **B** |
| Next 15 async `params` | `await ctx.params` everywhere | Runner awaits once | **B** |
| Implementation complexity | Low | Moderate (the fold) | **A** |

## Decision

Adopt **Convention B**. The only edge Convention A holds is internal simplicity,
and that cost is paid **once** in a vetted shared runner rather than by every
route author. The fold is advanced TypeScript, so it is shipped as an asset and
pinned with a type test — engineers consume it, they don't re-derive it.

Convention A is retained **only** as the `compose(...guards)(handler)` escape
hatch (same runner, HOF shape) for teams that explicitly prefer composition.

## Consequences

- One canonical pattern to learn; routes are auditable at a glance.
- A small amount of tricky type machinery to maintain — guarded by
  `guards-types.test-d.ts`; do not edit the fold without re-running `tsc`.
- Cross-cutting output (envelope, correlation id, audit) is centralized, so it
  is consistent and cannot be forgotten per route.
- Migration from the old wrappers is mechanical (`MIGRATION_FROM_HOF.md`).
