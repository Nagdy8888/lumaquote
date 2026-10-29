/**
 * @file shared/api/adapters/upstash-idempotency.ts
 * Default idempotency adapter on Upstash Redis. Reserves a key with a `SET NX`
 * lock, stores the serialized success response, and replays it for retries with
 * the same `Idempotency-Key`. Serverless-safe (shared across isolates).
 *
 * Requires: `@upstash/redis`.
 */
import { Redis } from "@upstash/redis"
import type { IdempotencyAdapter, IdempotencyReservation } from "@/shared/api/adapters/types"

/** Options for {@link upstashIdempotency}. */
export interface UpstashIdempotencyOptions {
  /** A pre-built client; if omitted one is built from url/token. */
  redis?: Redis
  /** REST URL. Defaults to `UPSTASH_REDIS_REST_URL`. */
  url?: string
  /** REST token. Defaults to `UPSTASH_REDIS_REST_TOKEN`. */
  token?: string
}

/** The serialized form of a stored response. */
interface StoredResponse {
  status: number
  headers: [string, string][]
  body: string
}

/** Resolve a Redis client from explicit options or environment. */
function resolveRedis(options: UpstashIdempotencyOptions): Redis {
  if (options.redis) return options.redis
  const url = options.url ?? process.env.UPSTASH_REDIS_REST_URL
  const token = options.token ?? process.env.UPSTASH_REDIS_REST_TOKEN
  if (!url || !token) {
    throw new Error("upstashIdempotency: missing UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN")
  }
  return new Redis({ url, token })
}

/** Reconstruct a Response from its stored form. */
function deserialize(stored: StoredResponse): Response {
  return new Response(stored.body, { status: stored.status, headers: stored.headers })
}

/**
 * Build an Upstash-backed {@link IdempotencyAdapter}.
 *
 * @param options - a Redis client or url/token
 * @returns an idempotency adapter
 */
export function upstashIdempotency(options: UpstashIdempotencyOptions = {}): IdempotencyAdapter {
  const redis = resolveRedis(options)
  return {
    async reserve(key, ttlMs): Promise<IdempotencyReservation> {
      const resultKey = `${key}:res`
      const lockKey = `${key}:lock`

      const stored = await redis.get<StoredResponse>(resultKey)
      if (stored) {
        return { replay: deserialize(stored), pending: false, save: async function noop() {} }
      }

      const locked = await redis.set(lockKey, "1", { nx: true, px: ttlMs })
      if (locked !== "OK") {
        return { replay: null, pending: true, save: async function noop() {} }
      }

      return {
        replay: null,
        pending: false,
        async save(response) {
          const headers: [string, string][] = []
          response.headers.forEach(function collect(value, key) {
            headers.push([key, value])
          })
          const serialized: StoredResponse = {
            status: response.status,
            headers,
            body: await response.text(),
          }
          await redis.set(resultKey, serialized, { px: ttlMs })
        },
      }
    },
  }
}
