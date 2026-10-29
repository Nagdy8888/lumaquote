/**
 * @file shared/api/guards/auth.ts
 * Authentication guards. `auth()` requires a verified session and adds a
 * non-null `principal` to the context; `optionalAuth()` attaches the principal
 * when present but never rejects. The principal comes from the configured
 * AuthAdapter (the verified session) — never from a request header.
 */
import { getAuthAdapter } from "@/shared/api/config"
import { fail } from "@/shared/api/respond"
import type { Guard, Principal } from "@/shared/api/types"

/**
 * Require a verified session. Returns 401 when there is none; otherwise adds
 * `{ principal }` to the context for downstream guards and the handler.
 *
 * @returns a guard that contributes a non-null {@link Principal}
 */
export function auth(): Guard<object, { principal: Principal }> {
  return {
    name: "auth",
    async run(ctx) {
      const principal = await getAuthAdapter().getPrincipal(ctx.req)
      if (!principal) {
        return fail(ctx, 401, "unauthorized", "Authentication required")
      }
      return { principal }
    },
  }
}

/**
 * Attach the principal when a session exists, but never reject. Useful for
 * endpoints that behave differently for signed-in vs anonymous callers.
 *
 * @returns a guard that contributes `{ principal: Principal | null }`
 */
export function optionalAuth(): Guard<object, { principal: Principal | null }> {
  return {
    name: "optionalAuth",
    async run(ctx) {
      const principal = await getAuthAdapter().getPrincipal(ctx.req)
      return { principal }
    },
  }
}
