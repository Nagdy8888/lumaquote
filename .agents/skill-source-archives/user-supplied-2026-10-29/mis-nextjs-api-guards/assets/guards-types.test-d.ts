/**
 * @file shared/api/guards-types.test-d.ts
 * Compile-time type tests that pin the inference contract: `ctx.principal` is
 * non-null after `auth()`, `ctx.body`/`ctx.params` are typed after `validate()`,
 * and additions are absent when their guard is omitted. These never run — they
 * pass iff the file type-checks (`tsc --noEmit`). If a future edit collapses the
 * fold, one of these lines turns red.
 */
import { z } from "zod"
import { defineRoute } from "@/shared/api/run-route"
import { auth } from "@/shared/api/guards/auth"
import { validate } from "@/shared/api/guards/validate"
import type { Principal } from "@/shared/api/types"

/** True iff `A` and `B` are the exact same type. */
type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <T>() => T extends B ? 1 : 2
  ? true
  : false
/** Compile error unless `T` is `true`. */
type Expect<T extends true> = T

const Body = z.object({ name: z.string(), count: z.number() })
const Params = z.object({ id: z.string().uuid() })

// auth() makes ctx.principal a non-null Principal; validate() types body + params.
defineRoute({
  guards: [auth(), validate({ body: Body, params: Params })],
  handler: async function typedHandler(_req, ctx) {
    type PrincipalIsNonNull = Expect<Equal<typeof ctx.principal, Principal>>
    type BodyIsInferred = Expect<Equal<typeof ctx.body, { name: string; count: number }>>
    type ParamsIdIsString = Expect<Equal<typeof ctx.params.id, string>>
    const _checks: [PrincipalIsNonNull, BodyIsInferred, ParamsIdIsString] = [true, true, true]
    void _checks
    return new Response()
  },
})

// Without auth(), there is no principal on the context.
defineRoute({
  guards: [validate({ body: Body })],
  handler: async function noAuthHandler(_req, ctx) {
    // @ts-expect-error — principal is absent without auth()
    void ctx.principal
    type BodyStillInferred = Expect<Equal<typeof ctx.body, { name: string; count: number }>>
    const _check: BodyStillInferred = true
    void _check
    return new Response()
  },
})

// Without validate(), there is no body on the context.
defineRoute({
  guards: [auth()],
  handler: async function noValidateHandler(_req, ctx) {
    // @ts-expect-error — body is absent without validate({ body })
    void ctx.body
    return new Response()
  },
})
