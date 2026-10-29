/**
 * @file shared/api/guards/timeout.ts
 * Timeout guard. Records a time budget that the runner uses to race the
 * handler; if the handler exceeds it, the runner aborts with a 504. The guard
 * itself only stores the budget — enforcement lives in the runner because a
 * guard cannot wrap the handler it precedes.
 */
import type { GuardContext, Guard } from "@/shared/api/types"

/**
 * Bound the handler's execution time. On overrun the runner returns 504. Useful
 * in front of slow upstreams (e.g. a Google Apps Script call — set 60–120s).
 *
 * @param ms - the handler time budget in milliseconds
 * @returns a guard that registers the timeout for the runner to enforce
 */
export function timeout(ms: number): Guard<object, object> {
  return {
    name: "timeout",
    run(ctx: GuardContext) {
      ctx.state.timeoutMs = ms
    },
  }
}
