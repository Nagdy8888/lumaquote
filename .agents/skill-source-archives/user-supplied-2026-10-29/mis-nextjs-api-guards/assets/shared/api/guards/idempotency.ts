/**
 * @file shared/api/guards/idempotency.ts
 * Idempotency guard. For retryable mutations, clients send an `Idempotency-Key`
 * header; the guard replays the stored response for a known key, rejects a
 * key that is still in flight (409), and otherwise registers a post-response
 * hook to persist the successful result. Requires an IdempotencyAdapter.
 */
import { getIdempotencyAdapter } from "@/shared/api/config"
import { fail } from "@/shared/api/respond"
import type { GuardContext, Guard } from "@/shared/api/types"

/** Default methods treated as idempotency-eligible. */
const DEFAULT_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

/** Options for {@link idempotency}. */
export interface IdempotencyOptions {
  /** Header carrying the key. Defaults to `idempotency-key`. */
  header?: string
  /** How long a key + its stored response live, in ms. Defaults to 24h. */
  ttlMs?: number
  /** Methods to apply idempotency to. Defaults to POST/PUT/PATCH/DELETE. */
  methods?: string[]
}

/**
 * Deduplicate retried mutations by `Idempotency-Key`. Requests without the
 * header pass through unchanged.
 *
 * @param options - header name, TTL, and eligible methods
 * @returns a guard that replays / dedupes idempotent mutations
 */
export function idempotency(options: IdempotencyOptions = {}): Guard<object, object> {
  const header = (options.header ?? "idempotency-key").toLowerCase()
  const ttlMs = options.ttlMs ?? 24 * 60 * 60 * 1000
  const methods = (options.methods ?? DEFAULT_METHODS).map(function upper(verb) {
    return verb.toUpperCase()
  })
  return {
    name: "idempotency",
    async run(ctx: GuardContext) {
      if (!methods.includes(ctx.req.method.toUpperCase())) return
      const key = ctx.req.headers.get(header)
      if (!key) return

      const namespaced = `idem:${new URL(ctx.req.url).pathname}:${key}`
      const reservation = await getIdempotencyAdapter().reserve(namespaced, ttlMs)

      if (reservation.replay) {
        return reservation.replay
      }
      if (reservation.pending) {
        return fail(ctx, 409, "conflict", "A request with this Idempotency-Key is already in progress")
      }

      // Newly reserved: persist the result once the handler succeeds.
      ctx.onResponse(async function saveIdempotentResult(response) {
        if (response.status < 300) {
          await reservation.save(response.clone())
        }
      })
    },
  }
}
