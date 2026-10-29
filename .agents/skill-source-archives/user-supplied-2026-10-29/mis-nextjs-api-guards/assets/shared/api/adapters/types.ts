/**
 * @file shared/api/adapters/types.ts
 * Pluggable backend contracts. Routes never name a concrete backend — they use
 * guards, and the guards read whichever adapter was wired once at boot via
 * `configureGuards`. Swap Supabase for another auth provider, or Upstash for a
 * different store, by changing one config call — no route changes.
 */
import type { NextRequest } from "next/server"
import type { Principal } from "@/shared/api/types"

/** Resolves the verified caller from a request. */
export interface AuthAdapter {
  /**
   * Resolve the principal from the *verified session only* (never a header).
   *
   * @param req - the incoming request
   * @returns the {@link Principal}, or `null` when there is no valid session
   */
  getPrincipal(req: NextRequest): Promise<Principal | null>
}

/** Outcome of counting one hit against a rate-limit window. */
export interface RateLimitResult {
  /** Whether this hit is within the limit. */
  success: boolean
  /** The configured ceiling for the window. */
  limit: number
  /** Hits remaining in the current window (never negative). */
  remaining: number
  /** Epoch milliseconds when the window resets. */
  reset: number
}

/** A distributed (serverless-safe) rate limiter. */
export interface RateLimitAdapter {
  /**
   * Atomically count one hit for `key` within `windowMs`.
   *
   * @param key - identity to throttle (IP, principal id, or composite)
   * @param limit - max hits allowed per window
   * @param windowMs - window length in milliseconds
   * @returns the {@link RateLimitResult}
   */
  hit(key: string, limit: number, windowMs: number): Promise<RateLimitResult>
}

/** A reservation returned when claiming an idempotency key. */
export interface IdempotencyReservation {
  /** A previously-stored response for this key to replay, or `null` if newly reserved. */
  replay: Response | null
  /** True when another request currently holds this key (still in flight). */
  pending: boolean
  /**
   * Persist the final response under the key for future replays.
   *
   * @param response - the completed response to store
   */
  save(response: Response): Promise<void>
}

/** Stores responses keyed by `Idempotency-Key` so retried mutations don't double-apply. */
export interface IdempotencyAdapter {
  /**
   * Claim `key`, returning any stored replay or a pending flag.
   *
   * @param key - the client-supplied idempotency key (namespaced by the guard)
   * @param ttlMs - how long the reservation/result lives
   * @returns the {@link IdempotencyReservation}
   */
  reserve(key: string, ttlMs: number): Promise<IdempotencyReservation>
}
