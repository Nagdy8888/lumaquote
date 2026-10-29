/**
 * @file shared/api/adapters/console-logger.ts
 * Default structured logger — emits one JSON line per call. `child()` carries
 * permanent bindings (e.g. the requestId) onto every subsequent line. Swap for
 * pino/winston in high-throughput services via `configureGuards({ logger })`.
 */
import type { Logger } from "@/shared/api/types"

/** Severity levels, ordered low → high. */
type Level = "debug" | "info" | "warn" | "error"

/** Emit one structured JSON log line. */
function emit(
  level: Level,
  bindings: Record<string, unknown>,
  message: string,
  fields?: Record<string, unknown>,
): void {
  const line = { level, time: new Date().toISOString(), message, ...bindings, ...fields }
  const sink = level === "error" || level === "warn" ? console.error : console.log
  sink(JSON.stringify(line))
}

/**
 * Build a console-backed {@link Logger}.
 *
 * @param bindings - fields included on every line (extended by `child`)
 * @returns a structured logger
 */
export function consoleLogger(bindings: Record<string, unknown> = {}): Logger {
  return {
    debug(message, fields) {
      emit("debug", bindings, message, fields)
    },
    info(message, fields) {
      emit("info", bindings, message, fields)
    },
    warn(message, fields) {
      emit("warn", bindings, message, fields)
    },
    error(message, fields) {
      emit("error", bindings, message, fields)
    },
    child(extra) {
      return consoleLogger({ ...bindings, ...extra })
    },
  }
}
