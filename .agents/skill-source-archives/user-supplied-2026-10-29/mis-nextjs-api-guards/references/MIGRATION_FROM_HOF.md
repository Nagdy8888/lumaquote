# Migrating from `withAuth` / `withRole` wrappers

A mechanical path from the old composable-HOF approach (`with-auth.ts`) to the
declarative pipeline. The semantics are preserved — only the shape changes.

## Wrapper → guard map

| Old | New | Notes |
|---|---|---|
| `withAuth(handler)` | `auth()` | principal still from the verified session only |
| `withRole("admin")(handler)` | `roles("admin")` | ADMIN bypass preserved; empty = admin-only |
| `withOwnership(load)(handler)` | `ownership(load)` | loader now returns `{ ownerId, resource }` (resource exposed as `ctx.resource`) |
| `withValidation(schema)(handler)` | `validate({ body: schema })` | flattened Zod error preserved in `error.details` |
| `fail(msg, status, details?)` | `fail(ctx, status, code, msg, details?)` | now takes `ctx` + a stable `code` |
| (none) | `rateLimit`, `cors`, `origin`, `idempotency`, `timeout`, `permissions`, `audit` | new capabilities |

## Handler signature

Old wrappers passed `principal` (and `data`) as positional args:

```ts
// OLD
async function handler(req: NextRequest, principal: UserData, data: T, ctx: RouteContext)
```

New handlers take `(req, ctx)`; everything is on the typed `ctx`:

```ts
// NEW
async function handler(_req, ctx) {
  ctx.principal   // was `principal`
  ctx.body        // was `data`
  ctx.params      // was `ctx.params` (already awaited by the runner)
}
```

## Before / after

**Before** (old `with-auth.ts` style):

```ts
export const POST = withAuth(
  withRole("admin", "manager")(
    withValidation(CreateOrderSchema)(
      async (req, principal, data, ctx) => {
        const order = await createOrder(principal.id, data)
        return Response.json(order, { status: 201 })
      },
    ),
  ),
)
```

**After**:

```ts
export const POST = defineRoute({
  guards: [
    auth(),
    roles("admin", "manager"),
    validate({ body: CreateOrderSchema }),
  ],
  handler: async function createOrderHandler(_req, ctx) {
    const order = await createOrder(ctx.principal.id, ctx.body)
    return ok(ctx, order, { status: 201 })
  },
})
```

**Ownership before/after**:

```ts
// BEFORE
withAuth(withOwnership(async (req, principal, ctx) => {
  const doc = await getDoc(ctx.params.id)
  return doc ? { ownerId: doc.ownerId } : null
})(async (req, principal, ctx) => Response.json(await getDoc(ctx.params.id))))

// AFTER — load once, reuse via ctx.resource
defineRoute({
  guards: [
    auth(),
    validate({ params: z.object({ id: z.string().uuid() }) }),
    ownership(async (ctx) => {
      const doc = await getDoc(ctx.params.id)
      return doc ? { ownerId: doc.ownerId, resource: doc } : null
    }),
  ],
  handler: async (_req, ctx) => ok(ctx, ctx.resource),
})
```

## If a team really wants the HOF shape

The `compose` escape hatch keeps function composition while using the new runner
(envelope, correlation, audit, typed `ctx` all intact):

```ts
import { compose } from "@/shared/api/run-route"
export const POST = compose(auth(), roles("admin"), validate({ body: Schema }))(
  async function handler(_req, ctx) {
    return ok(ctx, await create(ctx.principal.id, ctx.body))
  },
)
```

Prefer `defineRoute`; `compose` exists for incremental migration and personal
preference, not as the standard.

## Migration steps

1. Drop the `assets/shared/api/` tree into `src/shared/api/`.
2. Add `configureGuards(...)` at boot (`shared/api/bootstrap.ts` +
   `instrumentation.ts`) — see `ADAPTERS.md`. Point `auth` at your existing
   session/role lookup via `mapUser`.
3. Convert routes one verb at a time using the table above. The wrappers and the
   pipeline can coexist during migration — do it incrementally.
4. Replace hand-built responses with `ok()`/`fail()` or thrown `ApiError`s.
5. Delete `with-auth.ts` once no route imports it.
