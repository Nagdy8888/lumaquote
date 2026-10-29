/**
 * @file app/api/orders/[id]/route.ts
 * Example guarded route. Shows the canonical `defineRoute` pattern: guards in
 * execution order, a thin handler that reads the typed context and delegates to
 * an entity/feature API. Copy + adapt; delete the guards you don't need.
 */
import { z } from "zod"
import { ok } from "@/shared/api/respond"
import { defineRoute } from "@/shared/api/run-route"
import { auth } from "@/shared/api/guards/auth"
import { ownership, roles } from "@/shared/api/guards/authorize"
import { rateLimit } from "@/shared/api/guards/rate-limit"
import { validate } from "@/shared/api/guards/validate"
// import { getOrder, updateOrder } from "@/entities/order"

const ParamsSchema = z.object({ id: z.string().uuid() })
const UpdateOrderSchema = z.object({ note: z.string().min(1).max(500) })

/**
 * GET /api/orders/:id — the owner (or an admin) reads their order.
 *
 * `ownership` loads the order and asserts the caller owns it; the loaded
 * resource is then available as `ctx.resource`, fully typed.
 */
export const GET = defineRoute({
  guards: [
    auth(),
    validate({ params: ParamsSchema }),
    ownership(async function loadOrder(ctx) {
      // const order = await getOrder(ctx.params.id)
      const order = { id: ctx.params.id, ownerId: ctx.principal.id, note: "demo" }
      return order ? { ownerId: order.ownerId, resource: order } : null
    }),
  ],
  handler: async function getOrderHandler(_req, ctx) {
    return ok(ctx, ctx.resource)
  },
})

/**
 * PATCH /api/orders/:id — admins/managers update an order's note.
 *
 * Reads `ctx.principal` (non-null after `auth`), `ctx.params.id` (typed by
 * `validate({ params })`), and `ctx.body.note` (typed by `validate({ body })`).
 */
export const PATCH = defineRoute({
  guards: [
    rateLimit({ window: "1m", limit: 20 }),
    auth(),
    roles("admin", "manager"),
    validate({ params: ParamsSchema, body: UpdateOrderSchema }),
  ],
  handler: async function patchOrderHandler(_req, ctx) {
    ctx.log.info("update_order", { orderId: ctx.params.id, actorId: ctx.principal.id })
    // const updated = await updateOrder(ctx.params.id, { note: ctx.body.note })
    const updated = { id: ctx.params.id, note: ctx.body.note }
    return ok(ctx, updated)
  },
})
