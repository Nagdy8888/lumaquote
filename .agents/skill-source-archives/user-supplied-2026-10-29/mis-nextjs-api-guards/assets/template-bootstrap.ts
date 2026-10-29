/**
 * @file shared/api/bootstrap.ts
 * Wire the guard backends once, at app boot. Import this for its side effect
 * from `instrumentation.ts` (`export { register } from ...`) or from the root
 * layout so it runs before any route handler. Swapping a backend here changes
 * every route — no route edits.
 */
import { configureGuards } from "@/shared/api/config"
import { supabaseAuth } from "@/shared/api/adapters/supabase-auth"
import { upstashRateLimit } from "@/shared/api/adapters/upstash-rate-limit"
import { upstashIdempotency } from "@/shared/api/adapters/upstash-idempotency"
import { inMemoryRateLimit } from "@/shared/api/adapters/in-memory-rate-limit"
import type { Principal } from "@/shared/api/types"

const isProd = process.env.NODE_ENV === "production"

configureGuards({
  auth: supabaseAuth({
    /** Map the verified Supabase user to your Principal — pull roles from your DB. */
    async mapUser(user): Promise<Principal> {
      // const profile = await getProfile(user.id)
      return {
        id: user.id,
        email: user.email,
        roles: ["user"], // ← replace with profile.roles
        permissions: [],
      }
    },
  }),
  // Distributed in prod; per-process in dev (and clearly not for production).
  rateLimit: isProd ? upstashRateLimit() : inMemoryRateLimit(),
  idempotency: upstashIdempotency(),
  // logger defaults to consoleLogger(); swap for pino here if desired.
})
