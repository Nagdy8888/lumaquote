/**
 * @file shared/api/run-route.ts
 * The route runner — the single place that builds the per-request context,
 * runs guards in array order, owns the error envelope + `X-Request-Id` header +
 * audit log, then calls the handler. `defineRoute` is the primary API;
 * `compose` is a thin HOF escape hatch for teams that prefer function
 * composition. Both delegate to the same `execute`, so behaviour is identical.
 */
import type { NextRequest } from "next/server"
import { getLogger } from "@/shared/api/config"
import { isApiError, TimeoutError } from "@/shared/api/errors"
import { fail, fromApiError } from "@/shared/api/respond"
import type {
  Guard,
  GuardContext,
  NextRouteContext,
  NextRouteHandler,
  RouteContextFor,
} from "@/shared/api/types"

const REQUEST_ID_HEADER = "x-request-id"

/** A handler that receives the fully-refined context for the given guard tuple. */
export type RouteHandler<G extends readonly Guard[]> = (
  req: NextRequest,
  ctx: RouteContextFor<G>,
) => Response | Promise<Response>

/** Configuration object passed to {@link defineRoute}. */
export interface RouteConfig<G extends readonly Guard[]> {
  /** Guards run in array order; each may enrich the context or short-circuit. */
  guards: G
  /** The handler, called only if every guard passes. */
  handler: RouteHandler<G>
}

/** Best-effort client IP from forwarding headers. */
function resolveIp(req: NextRequest): string | null {
  const forwarded = req.headers.get("x-forwarded-for")
  if (forwarded) {
    const first = forwarded.split(",")[0]
    return first ? first.trim() : null
  }
  return req.headers.get("x-real-ip")
}

/** Post-response interceptors registered via `ctx.onResponse`. */
type ResponseHook = (response: Response) => void | Promise<void>

/** Build the initial context: correlation id, IP, awaited params, bound logger. */
async function buildContext(
  req: NextRequest,
  nextCtx: NextRouteContext,
  hooks: ResponseHook[],
): Promise<GuardContext> {
  const inbound = req.headers.get(REQUEST_ID_HEADER)
  const requestId = inbound && inbound.length > 0 ? inbound : crypto.randomUUID()
  const params = await nextCtx.params
  return {
    req,
    requestId,
    ip: resolveIp(req),
    params,
    log: getLogger().child({ requestId }),
    startedAt: performance.now(),
    responseHeaders: new Headers(),
    onResponse(hook) {
      hooks.push(hook)
    },
    state: {},
  }
}

/** Run guards in order; return the first short-circuit `Response`, or `null`. */
async function runGuardChain(ctx: GuardContext, guards: readonly Guard[]): Promise<Response | null> {
  for (const guard of guards) {
    const outcome = await guard.run(ctx)
    if (outcome instanceof Response) return outcome
    if (outcome && typeof outcome === "object") {
      Object.assign(ctx, outcome)
    }
  }
  return null
}

/** Merge guard-contributed headers + the correlation id onto the final response. */
function finalize(res: Response, ctx: GuardContext): Response {
  try {
    ctx.responseHeaders.forEach(function copyHeader(value, key) {
      res.headers.set(key, value)
    })
    res.headers.set(REQUEST_ID_HEADER, ctx.requestId)
  } catch {
    // Immutable headers (rare) — the body still carries requestId.
  }
  return res
}

/** Reject after `ms` with a {@link TimeoutError}; used to bound the handler. */
function withTimeout<T>(work: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>(function race(resolve, reject) {
    const timer = setTimeout(function onTimeout() {
      reject(new TimeoutError())
    }, ms)
    work.then(
      function onResolve(value) {
        clearTimeout(timer)
        resolve(value)
      },
      function onReject(err: unknown) {
        clearTimeout(timer)
        reject(err instanceof Error ? err : new Error(String(err)))
      },
    )
  })
}

/** Always-on audit line: method, path, status, latency, correlation id. */
function audit(ctx: GuardContext, status: number, shortCircuited: boolean): void {
  ctx.log.info("request", {
    method: ctx.req.method,
    path: new URL(ctx.req.url).pathname,
    status,
    durationMs: Math.round(performance.now() - ctx.startedAt),
    shortCircuited,
    ip: ctx.ip,
  })
}

/** Map a thrown value to a failure envelope (ApiError → its status; else 500). */
function handleError(ctx: GuardContext | null, err: unknown): Response {
  const requestId = ctx?.requestId ?? "unknown"
  const logger = ctx?.log ?? getLogger().child({ requestId })
  const res = isApiError(err)
    ? fromApiError({ requestId }, err)
    : fail({ requestId }, 500, "internal_error", "Internal server error")
  if (isApiError(err)) {
    logger.warn("api_error", { status: err.status, code: err.code })
  } else {
    logger.error("unhandled_error", { error: err instanceof Error ? err.message : String(err) })
  }
  return ctx ? finalize(res, ctx) : res
}

/** Run the registered post-response interceptors, swallowing hook errors. */
async function runResponseHooks(hooks: ResponseHook[], res: Response, ctx: GuardContext): Promise<void> {
  for (const hook of hooks) {
    try {
      await hook(res)
    } catch (err) {
      ctx.log.error("response_hook_failed", { error: err instanceof Error ? err.message : String(err) })
    }
  }
}

/** Shared execution path for both `defineRoute` and `compose`. */
async function execute<G extends readonly Guard[]>(
  req: NextRequest,
  nextCtx: NextRouteContext,
  guards: G,
  handler: RouteHandler<G>,
): Promise<Response> {
  const hooks: ResponseHook[] = []
  let ctx: GuardContext | null = null
  try {
    ctx = await buildContext(req, nextCtx, hooks)
    const shortCircuit = await runGuardChain(ctx, guards)

    let res: Response
    if (shortCircuit) {
      res = finalize(shortCircuit, ctx)
      audit(ctx, res.status, true)
    } else {
      // Safe cast: guards have run, so the context now carries every `Adds`.
      const timeoutMs = typeof ctx.state.timeoutMs === "number" ? ctx.state.timeoutMs : null
      const call = handler(req, ctx as RouteContextFor<G>)
      const handled = timeoutMs ? await withTimeout(Promise.resolve(call), timeoutMs) : await call
      res = finalize(handled, ctx)
      audit(ctx, res.status, false)
    }

    await runResponseHooks(hooks, res, ctx)
    return res
  } catch (err) {
    const res = handleError(ctx, err)
    if (ctx) await runResponseHooks(hooks, res, ctx)
    return res
  }
}

/**
 * Define a guarded route handler. Guards run top-to-bottom; the handler runs
 * only if all pass, receiving a context with every guard's additions inferred
 * (e.g. `ctx.principal` after `auth()`, `ctx.body` after `validate({ body })`).
 *
 * @param config - the guard tuple and the handler
 * @returns a handler with the exact signature Next.js calls for a `route.ts` verb
 */
export function defineRoute<const G extends readonly Guard[]>(
  config: RouteConfig<G>,
): NextRouteHandler {
  return async function routeHandler(req, nextCtx) {
    return execute(req, nextCtx, config.guards, config.handler)
  }
}

/**
 * HOF escape hatch for teams that prefer function composition over the config
 * object. `compose(auth(), roles("admin"))(handler)` is equivalent to
 * `defineRoute({ guards: [auth(), roles("admin")], handler })`.
 *
 * @param guards - the guard tuple, in execution order
 * @returns a wrapper that takes the handler and returns the Next.js handler
 */
export function compose<const G extends readonly Guard[]>(...guards: G) {
  return function withGuards(handler: RouteHandler<G>): NextRouteHandler {
    return async function routeHandler(req, nextCtx) {
      return execute(req, nextCtx, guards, handler)
    }
  }
}
