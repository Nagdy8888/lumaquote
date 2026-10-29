/**
 * @file shared/api/config.ts
 * The adapter registry. Call `configureGuards(...)` exactly once at app boot
 * (e.g. in `instrumentation.ts` or a `shared/api/bootstrap.ts` imported by the
 * root layout) to wire auth, rate-limit, idempotency, and logging backends.
 * Guards read these lazily, so a backend is only required when a guard that
 * uses it actually runs.
 */
import { consoleLogger } from "@/shared/api/adapters/console-logger"
import type {
  AuthAdapter,
  IdempotencyAdapter,
  RateLimitAdapter,
} from "@/shared/api/adapters/types"
import type { Logger } from "@/shared/api/types"

/** The set of backends a project may wire. Only `auth` and `logger` are commonly set. */
export interface GuardsConfig {
  /** Resolves the verified principal. Required for the `auth()` guard. */
  auth: AuthAdapter
  /** Distributed limiter. Required for the `rateLimit()` guard. */
  rateLimit: RateLimitAdapter
  /** Idempotency store. Required for the `idempotency()` guard. */
  idempotency: IdempotencyAdapter
  /** Root structured logger. Defaults to {@link consoleLogger}. */
  logger: Logger
}

const DEFAULT_LOGGER: Logger = consoleLogger()

let registry: Partial<GuardsConfig> = {}

/**
 * Wire the guard backends. Last call wins; call once at boot.
 *
 * @param config - the adapters to register (any subset)
 */
export function configureGuards(config: Partial<GuardsConfig>): void {
  registry = config
}

/**
 * The root logger, falling back to the console logger when unconfigured.
 *
 * @returns the configured (or default) {@link Logger}
 */
export function getLogger(): Logger {
  return registry.logger ?? DEFAULT_LOGGER
}

/**
 * The configured auth adapter.
 *
 * @returns the {@link AuthAdapter}
 * @throws Error when the `auth()` guard runs without a configured adapter
 */
export function getAuthAdapter(): AuthAdapter {
  if (!registry.auth) {
    throw new Error(
      "auth() guard used but no AuthAdapter configured. " +
        "Call configureGuards({ auth: supabaseAuth() }) at app boot.",
    )
  }
  return registry.auth
}

/**
 * The configured rate-limit adapter.
 *
 * @returns the {@link RateLimitAdapter}
 * @throws Error when the `rateLimit()` guard runs without a configured adapter
 */
export function getRateLimitAdapter(): RateLimitAdapter {
  if (!registry.rateLimit) {
    throw new Error(
      "rateLimit() guard used but no RateLimitAdapter configured. " +
        "Call configureGuards({ rateLimit: upstashRateLimit({ ... }) }) at app boot.",
    )
  }
  return registry.rateLimit
}

/**
 * The configured idempotency adapter.
 *
 * @returns the {@link IdempotencyAdapter}
 * @throws Error when the `idempotency()` guard runs without a configured adapter
 */
export function getIdempotencyAdapter(): IdempotencyAdapter {
  if (!registry.idempotency) {
    throw new Error(
      "idempotency() guard used but no IdempotencyAdapter configured. " +
        "Call configureGuards({ idempotency: upstashIdempotency({ ... }) }) at app boot.",
    )
  }
  return registry.idempotency
}
