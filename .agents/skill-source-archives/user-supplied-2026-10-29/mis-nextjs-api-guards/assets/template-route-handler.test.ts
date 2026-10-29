/**
 * @file shared/api/route.test.ts
 * Example tests for the guard pipeline. Demonstrates the two levels: unit-test
 * a single guard by calling `guard.run(ctx)` directly (no HTTP), and end-to-end
 * test a `defineRoute` handler by invoking it with a `NextRequest`. Uses Vitest;
 * the in-memory adapters keep it hermetic.
 */
import { beforeAll, describe, expect, it } from "vitest"
import { NextRequest } from "next/server"
import { configureGuards } from "@/shared/api/config"
import { inMemoryRateLimit } from "@/shared/api/adapters/in-memory-rate-limit"
import { auth } from "@/shared/api/guards/auth"
import { roles } from "@/shared/api/guards/authorize"
import { rateLimit } from "@/shared/api/guards/rate-limit"
import { ok } from "@/shared/api/respond"
import { defineRoute } from "@/shared/api/run-route"
import type { GuardContext, Principal } from "@/shared/api/types"

/** Build a minimal in-memory context for unit-testing a single guard. */
function makeCtx(url: string, principal?: Principal): GuardContext & { principal?: Principal } {
  const noop = (): void => {}
  const log = { debug: noop, info: noop, warn: noop, error: noop, child: () => log }
  const ctx: GuardContext & { principal?: Principal } = {
    req: new NextRequest(url),
    requestId: "test-req",
    ip: "127.0.0.1",
    params: {},
    log,
    startedAt: 0,
    responseHeaders: new Headers(),
    onResponse: noop,
    state: {},
  }
  if (principal) ctx.principal = principal
  return ctx
}

describe("roles guard (unit)", () => {
  it("403s a caller missing the role", async () => {
    const ctx = makeCtx("https://x.test/api/orders/1", { id: "u1", roles: ["user"] })
    const result = await roles("admin").run(ctx as GuardContext & { principal: Principal })
    expect(result).toBeInstanceOf(Response)
    expect((result as Response).status).toBe(403)
  })

  it("passes an admin regardless of the requested role", async () => {
    const ctx = makeCtx("https://x.test/api/orders/1", { id: "u1", roles: ["admin"] })
    const result = await roles("manager").run(ctx as GuardContext & { principal: Principal })
    expect(result).toBeUndefined()
  })
})

describe("defineRoute (end-to-end)", () => {
  beforeAll(() => {
    configureGuards({
      auth: { async getPrincipal() { return { id: "u1", roles: ["admin"] } } },
      rateLimit: inMemoryRateLimit(),
    })
  })

  const GET = defineRoute({
    guards: [rateLimit({ window: "1m", limit: 2 }), auth()],
    handler: async function meHandler(_req, ctx) {
      return ok(ctx, { id: ctx.principal.id })
    },
  })

  it("runs guards then the handler, stamping correlation + rate-limit headers", async () => {
    const res = await GET(new NextRequest("https://x.test/api/me"), { params: Promise.resolve({}) })
    expect(res.status).toBe(200)
    expect(res.headers.get("x-request-id")).toBeTruthy()
    expect(res.headers.get("X-RateLimit-Limit")).toBe("2")
    await expect(res.json()).resolves.toMatchObject({ ok: true, data: { id: "u1" } })
  })

  it("429s once the window limit is exceeded", async () => {
    const hit = () => GET(new NextRequest("https://x.test/api/burst"), { params: Promise.resolve({}) })
    expect((await hit()).status).toBe(200)
    expect((await hit()).status).toBe(200)
    const limited = await hit()
    expect(limited.status).toBe(429)
    expect(limited.headers.get("Retry-After")).toBeTruthy()
  })
})
