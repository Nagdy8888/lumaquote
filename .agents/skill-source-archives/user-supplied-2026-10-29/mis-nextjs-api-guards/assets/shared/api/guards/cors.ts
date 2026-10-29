/**
 * @file shared/api/guards/cors.ts
 * Cross-origin guards: `cors()` answers preflights and adds the
 * `Access-Control-*` headers to every response (via `ctx.responseHeaders`), and
 * `origin()` rejects state-changing requests whose Origin isn't allowed — a
 * lightweight CSRF defense for cookie-authenticated mutations.
 */
import { fail } from "@/shared/api/respond"
import { NextResponse } from "next/server"
import type { GuardContext, Guard } from "@/shared/api/types"

/** Methods considered "safe" — not subject to the origin (CSRF) check. */
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"])

/** Options for {@link cors}. */
export interface CorsOptions {
  /** Allowed origins, or `"*"`. Defaults to `"*"`. */
  origins?: string[] | "*"
  /** Allowed methods. Defaults to the common set. */
  methods?: string[]
  /** Allowed request headers. Defaults to `Content-Type, Authorization`. */
  headers?: string[]
  /** Whether to allow credentials. Forces an explicit origin echo (never `*`). */
  credentials?: boolean
  /** Preflight cache duration in seconds. */
  maxAge?: number
}

/** Parse the host out of a URL/origin string, or null if unparseable. */
function hostOf(value: string | null): string | null {
  if (!value) return null
  try {
    return new URL(value).host
  } catch {
    return null
  }
}

/** Decide the value for `Access-Control-Allow-Origin`. */
function resolveAllowOrigin(origins: string[] | "*", requestOrigin: string | null): string | null {
  if (origins === "*") return "*"
  if (requestOrigin && origins.includes(requestOrigin)) return requestOrigin
  return null
}

/**
 * Apply CORS handling. On `OPTIONS` it short-circuits with a 204 preflight; on
 * every other method it stages the `Access-Control-*` headers so the runner
 * merges them onto the final response.
 *
 * @param options - allowed origins, methods, headers, credentials, max-age
 * @returns a guard handling preflight and CORS response headers
 */
export function cors(options: CorsOptions = {}): Guard<object, object> {
  const origins = options.origins ?? "*"
  const methods = options.methods ?? ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
  const headers = options.headers ?? ["Content-Type", "Authorization"]
  return {
    name: "cors",
    run(ctx: GuardContext) {
      const requestOrigin = ctx.req.headers.get("origin")
      const allowOrigin = resolveAllowOrigin(origins, requestOrigin)

      if (allowOrigin) {
        ctx.responseHeaders.set("Access-Control-Allow-Origin", options.credentials ? requestOrigin ?? allowOrigin : allowOrigin)
        ctx.responseHeaders.append("Vary", "Origin")
        if (options.credentials) {
          ctx.responseHeaders.set("Access-Control-Allow-Credentials", "true")
        }
      }

      if (ctx.req.method.toUpperCase() === "OPTIONS") {
        const preflight = new NextResponse(null, { status: 204 })
        preflight.headers.set("Access-Control-Allow-Methods", methods.join(", "))
        preflight.headers.set("Access-Control-Allow-Headers", headers.join(", "))
        if (options.maxAge !== undefined) {
          preflight.headers.set("Access-Control-Max-Age", String(options.maxAge))
        }
        return preflight
      }
    },
  }
}

/**
 * Reject state-changing requests whose Origin is not allowed. With no allowlist
 * it requires the Origin host to equal the request Host (same-origin). Returns
 * 403 on a missing or mismatched Origin.
 *
 * @param allowed - explicit allowed origins; omit for strict same-origin
 * @returns a guard enforcing the origin on mutations
 */
export function origin(allowed?: string[]): Guard<object, object> {
  return {
    name: "origin",
    run(ctx: GuardContext) {
      if (SAFE_METHODS.has(ctx.req.method.toUpperCase())) return
      const requestOrigin = ctx.req.headers.get("origin")
      if (!requestOrigin) {
        return fail(ctx, 403, "forbidden", "Missing Origin header on a state-changing request")
      }
      const originHost = hostOf(requestOrigin)
      const allowedHosts = allowed
        ? allowed.map(hostOf)
        : [ctx.req.headers.get("host")]
      if (!originHost || !allowedHosts.includes(originHost)) {
        return fail(ctx, 403, "forbidden", "Origin not allowed")
      }
    },
  }
}
