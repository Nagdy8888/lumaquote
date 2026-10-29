/**
 * @file shared/api/adapters/upstash-rate-limit.ts
 * Default rate-limit adapter: a fixed-window counter on Upstash Redis (REST).
 * Because Upstash is an HTTP/fetch service, this works on the Edge runtime and
 * across serverless isolates — every isolate shares the same counter, unlike an
 * in-process map.
 *
 * Requires: `@upstash/redis`.
 */
import { Redis } from "@upstash/redis"
import type { RateLimitAdapter, RateLimitResult } from "@/shared/api/adapters/types"

/** Options for {@link upstashRateLimit}. */
export interface UpstashRateLimitOptions {
  /** A pre-built client; if omitted one is built from url/token. */
  redis?: Redis
  /** REST URL. Defaults to `UPSTASH_REDIS_REST_URL`. */
  url?: string
  /** REST token. Defaults to `UPSTASH_REDIS_REST_TOKEN`. */
  token?: string
}

/** Resolve a Redis client from explicit options or environment. */
function resolveRedis(options: UpstashRateLimitOptions): Redis {
  if (options.redis) return options.redis
  const url = options.url ?? process.env.UPSTASH_REDIS_REST_URL
  const token = options.token ?? process.env.UPSTASH_REDIS_REST_TOKEN
  if (!url || !token) {
    throw new Error("upstashRateLimit: missing UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN")
  }
  return new Redis({ url, token })
}

/**
 * Build an Upstash-backed {@link RateLimitAdapter} (fixed window).
 *
 * @param options - a Redis client or url/token
 * @returns a distributed rate-limit adapter
 */
export function upstashRateLimit(options: UpstashRateLimitOptions = {}): RateLimitAdapter {
  const redis = resolveRedis(options)
  return {
    async hit(key, limit, windowMs): Promise<RateLimitResult> {
      const bucket = `rl:${key}`
      const count = await redis.incr(bucket)
      if (count === 1) {
        await redis.pexpire(bucket, windowMs)
      }
      const ttl = await redis.pttl(bucket)
      const reset = Date.now() + (ttl > 0 ? ttl : windowMs)
      return {
        success: count <= limit,
        limit,
        remaining: Math.max(0, limit - count),
        reset,
      }
    },
  }
}
