/**
 * @file shared/api/guards/rate-limit.ts
 * Rate-limiting guard. Throttles by IP (default), by principal, or by a custom
 * key, using the configured distributed RateLimitAdapter (Upstash by default,
 * so it works across serverless isolates). Adds `X-RateLimit-*` headers to the
 * response and returns 429 with `Retry-After` when the limit is exceeded.
 */
import { getRateLimitAdapter } from "@/shared/api/config"
import { fail } from "@/shared/api/respond"
import type { GuardContext, Guard, Principal } from "@/shared/api/types"

/** A window length: milliseconds, or a shorthand like `"1m"`, `"30s"`, `"1h"`, `"1d"`. */
export type RateWindow = number | `${number}s` | `${number}m` | `${number}h` | `${number}d`

/** How to derive the throttle key for a request. */
export type RateKeyBy = "ip" | "principal" | ((ctx: GuardContext) => string)

/** Options for {@link rateLimit}. */
export interface RateLimitOptions {
  /** Max requests allowed per window. */
  limit: number
  /** Window length (e.g. `"1m"` or `60_000`). */
  window: RateWindow
  /** What to key on. Defaults to `"ip"`. `"principal"` requires `auth()` first. */
  keyBy?: RateKeyBy
  /** Namespace prefix to isolate buckets per route/concern. Defaults to the path. */
  prefix?: string
}

const UNIT_MS: Record<string, number> = { s: 1000, m: 60_000, h: 3_600_000, d: 86_400_000 }

/** Convert a {@link RateWindow} to milliseconds. */
function windowToMs(window: RateWindow): number {
  if (typeof window === "number") return window
  const match = /^(\d+)([smhd])$/.exec(window)
  const value = match?.[1]
  const unit = match?.[2]
  if (!value || !unit) {
    throw new Error(`Invalid rate-limit window: "${window}" (use ms or "1m"/"30s"/"1h"/"1d")`)
  }
  const unitMs = UNIT_MS[unit]
  if (unitMs === undefined) {
    throw new Error(`Invalid rate-limit window unit: "${unit}"`)
  }
  return Number(value) * unitMs
}

/** Resolve the bucket key for this request. */
function resolveKey(ctx: GuardContext, keyBy: RateKeyBy): string {
  if (typeof keyBy === "function") return keyBy(ctx)
  if (keyBy === "principal") {
    const principal = (ctx as GuardContext & { principal?: Principal }).principal
    if (!principal) {
      throw new Error("rateLimit({ keyBy: 'principal' }) requires auth() earlier in the guard list")
    }
    return `user:${principal.id}`
  }
  return `ip:${ctx.ip ?? "unknown"}`
}

/**
 * Throttle requests against the configured distributed limiter.
 *
 * @param options - limit, window, and how to key the bucket
 * @returns a guard that returns 429 when the limit is exceeded
 */
export function rateLimit(options: RateLimitOptions): Guard<object, object> {
  const windowMs = windowToMs(options.window)
  const keyBy = options.keyBy ?? "ip"
  return {
    name: "rateLimit",
    async run(ctx) {
      const prefix = options.prefix ?? new URL(ctx.req.url).pathname
      const key = `${prefix}:${resolveKey(ctx, keyBy)}`
      const result = await getRateLimitAdapter().hit(key, options.limit, windowMs)

      ctx.responseHeaders.set("X-RateLimit-Limit", String(result.limit))
      ctx.responseHeaders.set("X-RateLimit-Remaining", String(result.remaining))
      ctx.responseHeaders.set("X-RateLimit-Reset", String(Math.ceil(result.reset / 1000)))

      if (!result.success) {
        const retryAfter = Math.max(0, Math.ceil((result.reset - Date.now()) / 1000))
        ctx.responseHeaders.set("Retry-After", String(retryAfter))
        return fail(ctx, 429, "rate_limited", "Too many requests")
      }
    },
  }
}
