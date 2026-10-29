/**
 * @file shared/api/adapters/supabase-auth.ts
 * Default auth adapter: verifies the Supabase session with `getUser()` (which
 * re-validates the JWT against the auth server — not the spoofable `getSession`)
 * and maps the verified user to your app's Principal. Role/permission resolution
 * is delegated to `mapUser`, because that lives in your database, not Supabase.
 *
 * Requires: `@supabase/ssr`, `@supabase/supabase-js`.
 */
import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"
import type { User } from "@supabase/supabase-js"
import type { AuthAdapter } from "@/shared/api/adapters/types"
import type { Principal } from "@/shared/api/types"

/** Options for {@link supabaseAuth}. */
export interface SupabaseAuthOptions {
  /**
   * Map the verified Supabase user to your Principal — attach roles/permissions
   * from your own tables here. Return value's `id`/`roles` drive RBAC.
   */
  mapUser: (user: User) => Principal | Promise<Principal>
  /** Supabase project URL. Defaults to `NEXT_PUBLIC_SUPABASE_URL`. */
  supabaseUrl?: string
  /** Supabase anon key. Defaults to `NEXT_PUBLIC_SUPABASE_ANON_KEY`. */
  supabaseAnonKey?: string
}

/**
 * Build a Supabase-backed {@link AuthAdapter}.
 *
 * @param options - the user→principal mapper and optional credentials
 * @returns an auth adapter that resolves the principal from the verified session
 */
export function supabaseAuth(options: SupabaseAuthOptions): AuthAdapter {
  const url = options.supabaseUrl ?? process.env.NEXT_PUBLIC_SUPABASE_URL
  const anonKey = options.supabaseAnonKey ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  return {
    async getPrincipal() {
      if (!url || !anonKey) {
        throw new Error("supabaseAuth: missing NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY")
      }
      const cookieStore = await cookies()
      const supabase = createServerClient(url, anonKey, {
        cookies: {
          getAll() {
            return cookieStore.getAll()
          },
          setAll() {
            // Route handlers don't refresh the session cookie; no-op.
          },
        },
      })
      const { data, error } = await supabase.auth.getUser()
      if (error || !data.user) return null
      return options.mapUser(data.user)
    },
  }
}
