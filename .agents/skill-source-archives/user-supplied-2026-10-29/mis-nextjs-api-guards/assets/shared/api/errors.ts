/**
 * @file shared/api/errors.ts
 * Typed API errors. Guards and domain code throw these; the runner renders any
 * thrown {@link ApiError} as a clean failure envelope with the right HTTP
 * status, and maps every *other* thrown value to a 500 `internal_error` (so
 * internals never leak). The subclasses mirror NestJS's HttpException family
 * for familiarity.
 */

/** Stable, machine-readable error codes returned in the failure envelope. */
export type ErrorCode =
  | "bad_request"
  | "validation_failed"
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "method_not_allowed"
  | "unsupported_media_type"
  | "payload_too_large"
  | "conflict"
  | "rate_limited"
  | "unavailable"
  | "timeout"
  | "upstream_error"
  | "internal_error"

/**
 * An error carrying an HTTP status and a stable {@link ErrorCode}. Throw this
 * (or a subclass) from anywhere in a guard or handler to short-circuit with a
 * consistent envelope instead of hand-building a `Response`.
 */
export class ApiError extends Error {
  /** HTTP status code to send. */
  readonly status: number
  /** Stable machine code for clients to branch on. */
  readonly code: ErrorCode
  /** Optional structured details (e.g. flattened validation issues). */
  readonly details?: unknown

  /**
   * @param status - HTTP status code
   * @param code - stable machine {@link ErrorCode}
   * @param message - human-readable message (safe to surface to clients)
   * @param details - optional structured details
   */
  constructor(status: number, code: ErrorCode, message: string, details?: unknown) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.code = code
    this.details = details
  }
}

/** 400 — malformed or semantically invalid request. */
export class BadRequestError extends ApiError {
  constructor(message = "Bad request", details?: unknown) {
    super(400, "bad_request", message, details)
    this.name = "BadRequestError"
  }
}

/** 400 — input failed schema validation; `details` carries the flattened issues. */
export class ValidationError extends ApiError {
  constructor(message = "Validation failed", details?: unknown) {
    super(400, "validation_failed", message, details)
    this.name = "ValidationError"
  }
}

/** 401 — no valid session / credentials. */
export class UnauthorizedError extends ApiError {
  constructor(message = "Unauthorized", details?: unknown) {
    super(401, "unauthorized", message, details)
    this.name = "UnauthorizedError"
  }
}

/** 403 — authenticated but not allowed. */
export class ForbiddenError extends ApiError {
  constructor(message = "Forbidden", details?: unknown) {
    super(403, "forbidden", message, details)
    this.name = "ForbiddenError"
  }
}

/** 404 — addressed resource does not exist (or is hidden from this caller). */
export class NotFoundError extends ApiError {
  constructor(message = "Not found", details?: unknown) {
    super(404, "not_found", message, details)
    this.name = "NotFoundError"
  }
}

/** 409 — conflict, e.g. an idempotency key already in flight. */
export class ConflictError extends ApiError {
  constructor(message = "Conflict", details?: unknown) {
    super(409, "conflict", message, details)
    this.name = "ConflictError"
  }
}

/** 429 — rate limit exceeded. */
export class RateLimitedError extends ApiError {
  constructor(message = "Too many requests", details?: unknown) {
    super(429, "rate_limited", message, details)
    this.name = "RateLimitedError"
  }
}

/** 502 — an upstream dependency (e.g. a GAS web app) failed. */
export class UpstreamError extends ApiError {
  constructor(message = "Upstream error", details?: unknown) {
    super(502, "upstream_error", message, details)
    this.name = "UpstreamError"
  }
}

/** 504 — the handler exceeded its time budget. */
export class TimeoutError extends ApiError {
  constructor(message = "Request timed out", details?: unknown) {
    super(504, "timeout", message, details)
    this.name = "TimeoutError"
  }
}

/**
 * Narrow an unknown thrown value to {@link ApiError}.
 *
 * @param err - any caught value
 * @returns true if `err` is an ApiError
 */
export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError
}
