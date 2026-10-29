/**
 * @file shared/api/types.ts
 * Core contracts for the declarative guard pipeline: the per-request
 * {@link GuardContext}, the {@link Guard} interface, the principal shape, and
 * the type-level fold ({@link AccumulateAdds}) that lets `defineRoute` infer
 * exactly what each guard contributes to the context. No runtime code lives
 * here — only types and the structural logger interface.
 */
import type { NextRequest } from "next/server"

/**
 * A request-scoped structured logger, pre-bound to the correlation id. The
 * default implementation is `consoleLogger`; swap it via {@link configureGuards}.
 */
export interface Logger {
  /** Log at debug level with optional structured fields. */
  debug(message: string, fields?: Record<string, unknown>): void
  /** Log at info level with optional structured fields. */
  info(message: string, fields?: Record<string, unknown>): void
  /** Log at warn level with optional structured fields. */
  warn(message: string, fields?: Record<string, unknown>): void
  /** Log at error level with optional structured fields. */
  error(message: string, fields?: Record<string, unknown>): void
  /** Return a child logger that permanently carries `bindings` on every line. */
  child(bindings: Record<string, unknown>): Logger
}

/**
 * The authenticated caller. Projects extend this (email, org, …) via the
 * `AuthAdapter`; the index signature keeps those extra fields type-safe
 * without `any`. Derived only from a verified session — never from a header.
 */
export interface Principal {
  /** Stable unique id of the caller. */
  readonly id: string
  /** Role names assigned to the caller (case-insensitive when checked). */
  readonly roles: readonly string[]
  /** Fine-grained permission keys, if the project models them (DRF-style). */
  readonly permissions?: readonly string[]
  /** Project-specific additional claims (email, orgId, …). */
  readonly [claim: string]: unknown
}

/**
 * Mutable, progressively-enriched per-request context — the rough equivalent
 * of NestJS's `ExecutionContext`. The runner constructs it once; each guard
 * may read it and contribute typed additions (see {@link Guard}). The handler
 * receives it fully refined with every guard's `Adds` folded in.
 */
export interface GuardContext {
  /** The incoming request. */
  readonly req: NextRequest
  /** Correlation id (inbound `x-request-id` header, or generated). On every log line and the response. */
  readonly requestId: string
  /** Best-effort client IP from `x-forwarded-for` / platform headers; `null` if unknown. */
  readonly ip: string | null
  /** Resolved route params — the runner awaits Next 15's promise once. Refined by `validate({ params })`. */
  params: Record<string, string>
  /** Request-scoped structured logger, pre-bound to {@link requestId}. */
  readonly log: Logger
  /** Monotonic start timestamp (ms) for latency measurement. */
  readonly startedAt: number
  /** Headers the runner merges onto the final response (set by `cors()`, `rateLimit()`, …). */
  readonly responseHeaders: Headers
  /**
   * Register an interceptor that runs after the response is produced — used by
   * `idempotency()` to persist the result. Hooks receive the final response.
   *
   * @param hook - callback invoked with the outgoing response
   */
  readonly onResponse: (hook: (response: Response) => void | Promise<void>) => void
  /** Escape-hatch bag for cross-guard data; prefer typed additions over this. */
  readonly state: Record<string, unknown>
}

/** A guard either passes (optionally adding `Adds`) or halts with a `Response`. */
export type GuardOutcome<Adds extends object> = void | undefined | Adds | Response

/**
 * A guard inspects the context, may enrich it, and may short-circuit the
 * request with a `Response`. `run` is declared as a method (not an arrow
 * property) on purpose: method parameters are bivariant, which lets a guard
 * that *requires* `Needs` (e.g. `roles()` needs `{ principal }`) still satisfy
 * the base `Guard` constraint used by `defineRoute`'s tuple.
 *
 * @typeParam Needs - context keys an earlier guard must have already added
 * @typeParam Adds  - context keys this guard contributes downstream
 */
export interface Guard<Needs extends object = object, Adds extends object = object> {
  /** Stable name for logging / debugging (e.g. `"auth"`, `"rateLimit"`). */
  readonly name: string
  /**
   * Run the guard. Return `undefined`/`void` to pass, an object to merge into
   * the context as {@link Adds}, or a `Response` to short-circuit.
   *
   * @param ctx - the context so far, guaranteed to contain {@link Needs}
   */
  run(ctx: GuardContext & Needs): GuardOutcome<Adds> | Promise<GuardOutcome<Adds>>
  /** Phantom marker — exists only in the type system to drive context inference. Never read at runtime. */
  readonly __types?: { needs: Needs; adds: Adds }
}

/** Extract the `Adds` of a single guard from its phantom marker. */
type AddsOf<G> = G extends { __types?: { adds: infer A } } ? NonNullable<A> : object

/**
 * Fold a tuple of guards into the single accumulated context-addition type by
 * intersecting every guard's `Adds`. This is what makes `ctx.principal`
 * non-null after `auth()` and `ctx.body` typed after `validate({ body })`,
 * inferred in one pass over a flat array rather than through nested generics.
 */
export type AccumulateAdds<G extends readonly unknown[]> = G extends readonly [
  infer Head,
  ...infer Tail,
]
  ? AddsOf<Head> & AccumulateAdds<Tail>
  : object

/** The fully-refined context the handler receives, given the guard tuple `G`. */
export type RouteContextFor<G extends readonly Guard[]> = GuardContext & AccumulateAdds<G>

/** The route context shape Next.js passes to a handler (params async in 15). */
export interface NextRouteContext {
  /** Dynamic route segment params, async since Next.js 15. */
  params: Promise<Record<string, string>>
}

/** The exact handler signature Next.js invokes for a `route.ts` verb export. */
export type NextRouteHandler = (req: NextRequest, ctx: NextRouteContext) => Promise<Response>
