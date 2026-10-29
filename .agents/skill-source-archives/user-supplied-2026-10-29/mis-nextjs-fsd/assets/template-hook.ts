/**
 * @file features/<feature-name>/model/use-<hook-name>.ts
 * <One-sentence summary of what this hook exposes and which feature it serves>.
 */
"use client"

import { useEffect, useState } from "react"
import type { User } from "@/entities/user"
import { fetchUser } from "@/entities/user"

/**
 * Return shape for {@link useUserProfile}.
 */
export interface UseUserProfileResult {
  /** The current user, or null while loading / on error. */
  user: User | null
  /** True while the initial fetch is in flight. */
  isPending: boolean
  /** The most recent error, or null. */
  error: Error | null
}

/**
 * Loads the user profile for the given id and tracks its loading / error state.
 *
 * @param userId - the id of the user to load
 * @returns the user plus `isPending` and `error` flags
 */
export function useUserProfile(userId: string): UseUserProfileResult {
  const [user, setUser] = useState<User | null>(null)
  const [isPending, setPending] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(function syncUserProfile() {
    let cancelled = false
    setPending(true)
    setError(null)

    /** Performs the async fetch and updates state if not cancelled. */
    async function loadUser() {
      try {
        const u = await fetchUser(userId)
        if (!cancelled) setUser(u)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e : new Error(String(e)))
      } finally {
        if (!cancelled) setPending(false)
      }
    }

    void loadUser()

    return function cancelUserProfileSync() {
      cancelled = true
    }
  }, [userId])

  return { user, isPending, error }
}
