import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { Session } from "@supabase/supabase-js";
import { useQueryClient } from "@tanstack/react-query";
import { auth } from "./client";

const SessionContext = createContext<{
  session: Session | null;
  loading: boolean;
}>({ session: null, loading: true });

/** Own staff session lifecycle and clear all remote data when the authenticated identity changes. */
export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const queryClient = useQueryClient();
  /** Subscribe once and detach on unmount; avoid retaining another staff member's cached data. */
  useEffect(
    /** Load and subscribe to staff sessions; detach the listener when the provider unmounts. */
    function subscribeToAuth() {
      /** Apply only the server-issued session and finish the initial session lookup. */
      auth.auth.getSession().then(
        /** Apply the initial server-issued session and finish the startup loading state. */
        function applyInitialSession({ data }) {
          setSession(data.session);
          setLoading(false);
        },
      );
      /** Clear identity-bound server state before exposing the new session. */
      const { data } = auth.auth.onAuthStateChange(
        /** Apply an Auth session change and clear cached data when the staff identity changes. */
        function sessionChanged(_event, next) {
          setSession(
            /** Compare staff identities before replacing state so a different user never inherits cached company records. */
            function replaceSession(previous) {
              if (previous?.user.id !== next?.user.id) queryClient.clear();
              return next;
            },
          );
          setLoading(false);
        },
      );
      /** Release the Supabase listener when the provider is removed. */
      return function unsubscribe() {
        data.subscription.unsubscribe();
      };
    },
    [queryClient],
  );
  return (
    <SessionContext.Provider value={{ session, loading }}>
      {children}
    </SessionContext.Provider>
  );
}

/** Return the staff session for query scoping; server-side membership still authorizes each operation. */
export function useSession() {
  return useContext(SessionContext);
}
