/**
 * @file shared/api/guards/http.ts
 * Low-cost HTTP hygiene guards: `method()` (allowed verbs), `contentType()`
 * (require a media type on mutations), and `bodyLimit()` (reject oversized
 * bodies by Content-Length). These run first in the canonical ordering so
 * cheap rejections never reach auth or the database.
 */
import { fail } from "@/shared/api/respond"
import type { GuardContext, Guard } from "@/shared/api/types"

/** Methods that never carry a request body. */
const BODYLESS = new Set(["GET", "HEAD", "OPTIONS"])

/**
 * Allow only the given HTTP methods. Returns 405 with an `Allow` header
 * otherwise. (Often redundant since `route.ts` exports one function per verb,
 * but useful when a single handler serves several.)
 *
 * @param allowed - permitted verbs (case-insensitive)
 * @returns a guard that enforces the method allowlist
 */
export function method(...allowed: string[]): Guard<object, object> {
  const set = allowed.map(function upper(verb) {
    return verb.toUpperCase()
  })
  return {
    name: "method",
    run(ctx: GuardContext) {
      if (!set.includes(ctx.req.method.toUpperCase())) {
        ctx.responseHeaders.set("Allow", set.join(", "))
        return fail(ctx, 405, "method_not_allowed", `Method ${ctx.req.method} not allowed`)
      }
    },
  }
}

/**
 * Require one of the given content types on body-carrying requests. Defaults to
 * `application/json`. Returns 415 otherwise.
 *
 * @param types - acceptable media types (matched as substrings of the header)
 * @returns a guard that enforces the request content type
 */
export function contentType(...types: string[]): Guard<object, object> {
  const allowed = types.length > 0 ? types : ["application/json"]
  return {
    name: "contentType",
    run(ctx: GuardContext) {
      if (BODYLESS.has(ctx.req.method.toUpperCase())) return
      const header = (ctx.req.headers.get("content-type") ?? "").toLowerCase()
      const matched = allowed.some(function includesType(type) {
        return header.includes(type.toLowerCase())
      })
      if (!matched) {
        return fail(ctx, 415, "unsupported_media_type", `Expected content-type: ${allowed.join(", ")}`)
      }
    },
  }
}

/**
 * Reject requests whose `Content-Length` exceeds `maxBytes`. Cheap header
 * check; the platform should still enforce a hard cap for chunked uploads.
 *
 * @param maxBytes - maximum allowed body size in bytes
 * @returns a guard that returns 413 for oversized bodies
 */
export function bodyLimit(maxBytes: number): Guard<object, object> {
  return {
    name: "bodyLimit",
    run(ctx: GuardContext) {
      const header = ctx.req.headers.get("content-length")
      if (header && Number(header) > maxBytes) {
        return fail(ctx, 413, "payload_too_large", `Body exceeds ${maxBytes} bytes`)
      }
    },
  }
}
