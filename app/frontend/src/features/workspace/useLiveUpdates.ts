import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/shared/api/client";
import { openEventStream, type StreamEvent } from "@/shared/api/events";
import { auth } from "@/shared/auth/client";
import { useSession } from "@/shared/auth/session";

const RECONNECT_AFTER_END_MS = 1000;
const BACKOFF_START_MS = 2000;
const BACKOFF_CAP_MS = 30000;

/**
 * Delay before reconnecting after the nth consecutive failure (n >= 1):
 * 2 s, 4 s, 8 s ... capped at 30 s. Pure; no side effects.
 */
export function reconnectDelay(failures: number): number {
  return Math.min(
    BACKOFF_CAP_MS,
    BACKOFF_START_MS * 2 ** Math.max(0, failures - 1),
  );
}

/**
 * Resolve after `ms` milliseconds or as soon as `signal` aborts, whichever is first.
 * Side effects: one timer, cleared on abort. Never rejects.
 */
function wait(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise(
    /** Start the timer and the abort listener that both end the wait. */
    function schedule(resolve) {
      /** Stop waiting early so an unmounted hook never leaves a pending timer. */
      function finish() {
        clearTimeout(timer);
        signal.removeEventListener("abort", finish);
        resolve();
      }
      const timer = setTimeout(finish, ms);
      signal.addEventListener("abort", finish, { once: true });
    },
  );
}

/**
 * Read the revision from a `refresh` event, or null when the payload is malformed.
 * Pure. The payload is never logged.
 */
function readRevision(event: StreamEvent): number | null {
  try {
    const revision = (JSON.parse(event.data) as { revision?: unknown })
      .revision;
    return typeof revision === "number" ? revision : null;
  } catch {
    return null;
  }
}

/**
 * Keep one authenticated event stream open until `signal` aborts.
 * Inputs: `signal` that ends the loop, `onRefresh` called when the company revision
 * changed (first sight counts as a change), `onConnection` told whether live updates
 * are working (true once a stream opens, false after an error, revocation or abort;
 * it stays true across the planned 1 s reconnect). Behavior: a normal end reconnects
 * after 1 s; an error reconnects
 * with 2 s, 4 s, 8 s ... capped at 30 s; a `revoked` event signs the user out and
 * stops. Authority: the token is read fresh from the Auth client on every
 * connection and sent only by `openEventStream`. Nothing is logged.
 */
async function followStream(
  signal: AbortSignal,
  onRefresh: () => void,
  onConnection: (open: boolean) => void,
): Promise<void> {
  let lastRevision: number | null = null;
  let failures = 0;
  while (!signal.aborted) {
    const connection = new AbortController();
    /** Propagate the outer abort to the current connection. */
    function abortConnection() {
      connection.abort();
    }
    signal.addEventListener("abort", abortConnection, { once: true });
    let revoked = false;
    let failed = false;
    try {
      const {
        data: { session },
      } = await auth.auth.getSession();
      if (!session) throw new ApiError("Sign in to receive live updates.", 401);
      await openEventStream({
        path: "/events",
        token: session.access_token,
        signal: connection.signal,
        /** Mark the stream open and reset the failure count after the server accepts it. */
        onOpen() {
          failures = 0;
          onConnection(true);
        },
        /** React to one server event: refresh on a new revision, sign out on revocation. */
        onEvent(event) {
          if (event.event === "revoked") {
            revoked = true;
            connection.abort();
          } else if (event.event === "refresh") {
            const revision = readRevision(event);
            if (revision !== null && revision !== lastRevision) {
              lastRevision = revision;
              onRefresh();
            }
          }
        },
      });
    } catch {
      failed = !signal.aborted && !revoked;
    } finally {
      signal.removeEventListener("abort", abortConnection);
    }
    // A planned end keeps the flag true through the 1 s reconnect so the label does not flicker.
    if (failed || revoked || signal.aborted) onConnection(false);
    if (revoked) {
      await auth.auth.signOut();
      return;
    }
    if (signal.aborted) return;
    if (failed) failures += 1;
    await wait(
      failed ? reconnectDelay(failures) : RECONNECT_AFTER_END_MS,
      signal,
    );
  }
}

/**
 * Keep the workspace and conversation caches fresh from the server event stream
 * while a staff session exists. Output: `{ connected }`, true only while a stream is
 * open, so callers can slow their fallback polling. Side effects: at most one
 * stream per mounted caller (mount it once, in the shell); invalidates the
 * `workspace` and `conversation` queries when the company revision changes; signs
 * out when the server reports revoked membership; aborts on unmount or when the
 * staff identity changes. Authority: the server authorizes the stream and rechecks
 * membership before every event; this hook only reacts to it.
 */
export function useLiveUpdates(): { connected: boolean } {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [connected, setConnected] = useState(false);
  const userId = session?.user.id;
  useEffect(
    /** Open and close the stream with the staff identity; stop cleanly on unmount. */
    function runStream() {
      if (!userId) return;
      const controller = new AbortController();
      void followStream(
        controller.signal,
        /** Invalidate every remote collection that the revision change may affect. */
        function refreshQueries() {
          void queryClient.invalidateQueries({ queryKey: ["workspace"] });
          void queryClient.invalidateQueries({ queryKey: ["conversation"] });
        },
        setConnected,
      );
      /** Abort the stream and clear the connected flag. */
      return function stopStream() {
        controller.abort();
        setConnected(false);
      };
    },
    [userId, queryClient],
  );
  return { connected };
}
