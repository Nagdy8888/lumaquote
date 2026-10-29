/**
 * @file shared/api/adapters/in-memory-rate-limit.ts
 * Dev/test rate-limit adapter: a fixed-window counter in a process-local Map.
 *
 * ⚠️ NOT distributed. Each serverless isolate / Node process keeps its own
 * counters, so on Vercel or any multi-instance deploy the effective limit is
 * (configured limit × instance count). Use {@link upstashRateLimit} in
 * production; reach for this only for local development and unit tests.
 */
import type { RateLimitAdapter, RateLimitResult } from "@/shared/api/adapters/types"

/** A single fixed-window bucket. */
interface Bucket {
  count: number
  reset: number
}

/**
 * Build a process-local {@link RateLimitAdapter}. Dev/test only.
 *
 * @returns an in-memory rate-limit adapter
 */
export function inMemoryRateLimit(): RateLimitAdapter {
  const buckets = new Map<string, Bucket>()
  return {
    async hit(key, limit, windowMs): Promise<RateLimitResult> {
      const now = Date.now()
      const existing = buckets.get(key)
      if (!existing || existing.reset <= now) {
        const reset = now + windowMs
        buckets.set(key, { count: 1, reset })
        return { success: 1 <= limit, limit, remaining: Math.max(0, limit - 1), reset }
      }
      existing.count += 1
      return {
        success: existing.count <= limit,
        limit,
        remaining: Math.max(0, limit - existing.count),
        reset: existing.reset,
      }
    },
  }
}
