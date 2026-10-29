/**
 * @file shared/api/respond.ts
 * The MIS API response envelope. Every route returns one of these shapes so
 * clients branch on a stable `ok` flag and machine `code` — never on prose.
 * `ok()` / `fail()` take the request id (carried on the context) so the
 * correlation id appears in the body; the runner additionally stamps it on the
 * `X-Request-Id` response header for every response, even short-circuits.
 */
import { NextResponse } from "next/server"
import { ApiError, type ErrorCode } from "@/shared/api/errors"
import type { GuardContext } from "@/shared/api/types"

/** Successful response body. */
export interface SuccessEnvelope<T> {
  /** Always `true` for success. */
  ok: true
  /** The payload. */
  data: T
  /** Correlation id, echoing the `X-Request-Id` header. */
  requestId: string
}

/** Failure response body. */
export interface FailureEnvelope {
  /** Always `false` for failure. */
  ok: false
  /** Machine-readable error. */
  error: {
    /** Stable code the client branches on. */
    code: ErrorCode | string
    /** Human-readable, client-safe message. */
    message: string
    /** Optional structured details (e.g. validation issues). */
    details?: unknown
  }
  /** Correlation id, echoing the `X-Request-Id` header. */
  requestId: string
}

/** Either shape of the envelope. */
export type Envelope<T> = SuccessEnvelope<T> | FailureEnvelope

/** The minimum a responder needs from the context. */
type WithRequestId = Pick<GuardContext, "requestId">

/**
 * Build a success envelope response.
 *
 * @param ctx - the request context (for the correlation id)
 * @param data - the payload
 * @param init - optional response init (default status 200)
 * @returns a `NextResponse` wrapping a {@link SuccessEnvelope}
 */
export function ok<T>(
  ctx: WithRequestId,
  data: T,
  init?: ResponseInit,
): NextResponse<SuccessEnvelope<T>> {
  return NextResponse.json(
    { ok: true, data, requestId: ctx.requestId },
    { status: 200, ...init },
  )
}

/**
 * Build a failure envelope response.
 *
 * @param ctx - the request context (for the correlation id)
 * @param status - HTTP status code
 * @param code - stable machine {@link ErrorCode}
 * @param message - human-readable, client-safe message
 * @param details - optional structured details
 * @returns a `NextResponse` wrapping a {@link FailureEnvelope}
 */
export function fail(
  ctx: WithRequestId,
  status: number,
  code: ErrorCode | string,
  message: string,
  details?: unknown,
): NextResponse<FailureEnvelope> {
  return NextResponse.json(
    { ok: false, error: { code, message, ...(details === undefined ? {} : { details }) }, requestId: ctx.requestId },
    { status },
  )
}

/**
 * Render a thrown {@link ApiError} as a failure envelope. Used by the runner;
 * also handy if a handler catches and wants to convert an ApiError itself.
 *
 * @param ctx - the request context (for the correlation id)
 * @param err - the error to render
 * @returns a `NextResponse` wrapping a {@link FailureEnvelope}
 */
export function fromApiError(ctx: WithRequestId, err: ApiError): NextResponse<FailureEnvelope> {
  return fail(ctx, err.status, err.code, err.message, err.details)
}
