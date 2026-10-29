/**
 * @file shared/api/guards/validate.ts
 * Input validation guard. `validate({ body, query, params })` parses each
 * provided surface with a Zod schema and adds the typed result to the context
 * (`ctx.body`, `ctx.query`, `ctx.params`). Only the schema's fields survive —
 * no mass-assignment. Returns 400 with flattened issues on failure.
 */
import { fail } from "@/shared/api/respond"
import type { Guard } from "@/shared/api/types"
import type { ZodType } from "zod"

/** Which request surfaces to validate. Provide only the ones you need. */
export interface ValidateConfig {
  /** Schema for the JSON body (consumes the request stream). */
  body?: ZodType
  /** Schema for the URL search params (parsed into a flat object). */
  query?: ZodType
  /** Schema for the route params. */
  params?: ZodType
}

/** Map a {@link ValidateConfig} to the context additions it contributes. */
type Validated<C extends ValidateConfig> = (C extends { body: ZodType<infer B> }
  ? { body: B }
  : object) &
  (C extends { query: ZodType<infer Q> } ? { query: Q } : object) &
  (C extends { params: ZodType<infer P> } ? { params: P } : object)

/** Flatten the search params into a plain record for schema parsing. */
function searchParamsToObject(url: string): Record<string, string> {
  const out: Record<string, string> = {}
  new URL(url).searchParams.forEach(function collect(value, key) {
    out[key] = value
  })
  return out
}

/**
 * Validate the configured request surfaces and expose the typed results.
 *
 * @typeParam C - the schema config (drives the inferred additions)
 * @param config - schemas for body / query / params
 * @returns a guard that adds the parsed, typed values to the context
 */
export function validate<const C extends ValidateConfig>(config: C): Guard<object, Validated<C>> {
  return {
    name: "validate",
    async run(ctx) {
      const adds: Record<string, unknown> = {}

      if (config.body) {
        const raw = await ctx.req.json().catch(function noBody() {
          return undefined
        })
        const parsed = config.body.safeParse(raw)
        if (!parsed.success) {
          return fail(ctx, 400, "validation_failed", "Body validation failed", parsed.error.flatten())
        }
        adds.body = parsed.data
      }

      if (config.query) {
        const parsed = config.query.safeParse(searchParamsToObject(ctx.req.url))
        if (!parsed.success) {
          return fail(ctx, 400, "validation_failed", "Query validation failed", parsed.error.flatten())
        }
        adds.query = parsed.data
      }

      if (config.params) {
        const parsed = config.params.safeParse(ctx.params)
        if (!parsed.success) {
          return fail(ctx, 400, "validation_failed", "Params validation failed", parsed.error.flatten())
        }
        adds.params = parsed.data
      }

      return adds as Validated<C>
    },
  }
}
