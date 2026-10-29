/**
 * @file shared/api/guards/gate.ts
 * Availability gates: `maintenance()` blocks a route during a maintenance
 * window, and `featureFlag()` blocks it when a flag is off. Both take a
 * predicate so the project wires its own flag/config source — no adapter
 * required. Each returns 503 when closed.
 */
import { fail } from "@/shared/api/respond"
import type { GuardContext, Guard } from "@/shared/api/types"

/** Options for {@link maintenance}. */
export interface MaintenanceOptions {
  /** Seconds to advertise in the `Retry-After` header. */
  retryAfterSeconds?: number
  /** Message returned to the client. */
  message?: string
}

/**
 * Close the route while `isActive()` resolves truthy. Returns 503.
 *
 * @param isActive - predicate that reports whether maintenance is on
 * @param options - retry hint and message
 * @returns a guard that gates the route on maintenance state
 */
export function maintenance(
  isActive: (ctx: GuardContext) => boolean | Promise<boolean>,
  options: MaintenanceOptions = {},
): Guard<object, object> {
  return {
    name: "maintenance",
    async run(ctx: GuardContext) {
      if (await isActive(ctx)) {
        if (options.retryAfterSeconds !== undefined) {
          ctx.responseHeaders.set("Retry-After", String(options.retryAfterSeconds))
        }
        return fail(ctx, 503, "unavailable", options.message ?? "Service temporarily unavailable for maintenance")
      }
    },
  }
}

/** Options for {@link featureFlag}. */
export interface FeatureFlagOptions {
  /** Message returned when the flag is off. */
  message?: string
}

/**
 * Open the route only while `isEnabled()` resolves truthy. Returns 503 when off.
 *
 * @param isEnabled - predicate that reports whether the feature is enabled
 * @param options - message shown when disabled
 * @returns a guard that gates the route on a feature flag
 */
export function featureFlag(
  isEnabled: (ctx: GuardContext) => boolean | Promise<boolean>,
  options: FeatureFlagOptions = {},
): Guard<object, object> {
  return {
    name: "featureFlag",
    async run(ctx: GuardContext) {
      if (!(await isEnabled(ctx))) {
        return fail(ctx, 503, "unavailable", options.message ?? "This feature is not available")
      }
    },
  }
}
