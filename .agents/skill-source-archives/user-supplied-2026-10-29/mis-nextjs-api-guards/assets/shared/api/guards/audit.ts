/**
 * @file shared/api/guards/audit.ts
 * Explicit audit guard. The runner already emits a baseline `request` log line
 * for every call; `audit()` adds a business-level `audit` entry carrying a tag
 * and the acting principal, emitted once the response is known. Place it after
 * `auth()` so the actor is populated.
 */
import type { GuardContext, Guard, Principal } from "@/shared/api/types"

/** Options for {@link audit}. */
export interface AuditOptions {
  /** A label for the audited action, e.g. `"orders.create"`. */
  tag?: string
  /** Include the principal id as `actorId`. Defaults to true. */
  actor?: boolean
}

/**
 * Emit a structured audit entry for the request, including the outcome status
 * and (by default) the acting principal.
 *
 * @param options - the audit tag and whether to record the actor
 * @returns a guard that logs an `audit` line after the response is produced
 */
export function audit(options: AuditOptions = {}): Guard<object, object> {
  return {
    name: "audit",
    run(ctx: GuardContext) {
      ctx.onResponse(function logAudit(response) {
        const principal = (ctx as GuardContext & { principal?: Principal }).principal
        ctx.log.info("audit", {
          tag: options.tag,
          method: ctx.req.method,
          path: new URL(ctx.req.url).pathname,
          status: response.status,
          actorId: options.actor === false ? undefined : principal?.id,
        })
      })
    },
  }
}
