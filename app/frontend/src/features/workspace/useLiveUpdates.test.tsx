import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { reconnectDelay, useLiveUpdates } from "./useLiveUpdates";

const signOut = vi.fn();
vi.mock("@/shared/auth/client", () => ({
  auth: {
    auth: {
      getSession: () =>
        Promise.resolve({ data: { session: { access_token: "token-1" } } }),
      signOut: () => signOut(),
    },
  },
}));
vi.mock("@/shared/auth/session", () => ({
  useSession: () => ({ session: { user: { id: "staff-1" } }, loading: false }),
}));

const encoder = new TextEncoder();

/** One open mock stream: push SSE text, end it normally, and observe its abort signal. */
type MockStream = {
  push(text: string): void;
  end(): void;
  signal: AbortSignal;
};

/** Install a fetch mock whose every call opens a controllable stream and records it. */
function installStreams() {
  const streams: MockStream[] = [];
  const fetchMock = vi.fn(
    (_url: string, init: { signal: AbortSignal }) =>
      new Promise<Response>((resolve) => {
        let controller!: ReadableStreamDefaultController<Uint8Array>;
        const body = new ReadableStream<Uint8Array>({
          /** Capture the controller so the test can push and close. */
          start(c) {
            controller = c;
          },
        });
        init.signal.addEventListener("abort", () =>
          controller.error(new DOMException("Aborted", "AbortError")),
        );
        streams.push({
          push: (text) => controller.enqueue(encoder.encode(text)),
          end: () => controller.close(),
          signal: init.signal,
        });
        resolve(new Response(body, { status: 200 }));
      }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return { streams, fetchMock };
}

/** Render the hook inside a query client whose invalidation calls can be counted. */
function renderLive() {
  const client = new QueryClient();
  const invalidate = vi.spyOn(client, "invalidateQueries");
  /** Provide the shared query client to the hook under test. */
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { ...renderHook(() => useLiveUpdates(), { wrapper }), invalidate };
}

beforeEach(() => {
  signOut.mockReset();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("reconnectDelay", () => {
  /** Failures back off 2 s, 4 s, 8 s ... and stop growing at 30 s. */
  it("doubles from 2 s and caps at 30 s", () => {
    expect([1, 2, 3, 4, 5, 6, 20].map(reconnectDelay)).toEqual([
      2000, 4000, 8000, 16000, 30000, 30000, 30000,
    ]);
  });
});

describe("useLiveUpdates", () => {
  /** Only a changed revision invalidates the workspace, conversation and inventory queries; the flag follows the stream. */
  it("invalidates only when the revision changes", async () => {
    const { streams } = installStreams();
    const { result, invalidate } = renderLive();
    await waitFor(() => expect(streams).toHaveLength(1));
    await waitFor(() => expect(result.current.connected).toBe(true));
    await act(async () => {
      streams[0].push('event: refresh\ndata: {"revision": 3}\n\n');
      streams[0].push('event: refresh\ndata: {"revision": 3}\n\n');
      streams[0].push('event: refresh\ndata: {"revision": 4}\n\n');
    });
    await waitFor(() => expect(invalidate).toHaveBeenCalledTimes(6));
    const keys = invalidate.mock.calls.map((call) => call[0]?.queryKey?.[0]);
    expect(keys).toEqual([
      "workspace",
      "conversation",
      "inventory",
      "workspace",
      "conversation",
      "inventory",
    ]);
  });

  /** Unmounting aborts the open stream and no new connection is made afterwards. */
  it("aborts on unmount and does not reconnect", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { streams, fetchMock } = installStreams();
    const { unmount } = renderLive();
    await waitFor(() => expect(streams).toHaveLength(1));
    unmount();
    expect(streams[0].signal.aborted).toBe(true);
    await vi.advanceTimersByTimeAsync(40000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  /** A normally ended stream reconnects after 1 s and keeps the connected flag true meanwhile. */
  it("reconnects 1 s after a normal end", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { streams, fetchMock } = installStreams();
    const { result } = renderLive();
    await waitFor(() => expect(streams).toHaveLength(1));
    await waitFor(() => expect(result.current.connected).toBe(true));
    await act(async () => streams[0].end());
    expect(result.current.connected).toBe(true);
    await vi.advanceTimersByTimeAsync(1100);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  /** A failed open backs off 2 s then 4 s, and shows not connected. */
  it("backs off after errors", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response("", { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderLive();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(result.current.connected).toBe(false);
    await vi.advanceTimersByTimeAsync(1900);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(200);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    // Second attempt happened near t = 2 s; the third is due 4 s later, near t = 6 s.
    await vi.advanceTimersByTimeAsync(3500);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(600);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  /** A revoked event signs the user out and stops without reconnecting. */
  it("signs out on revoked and stops", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { streams, fetchMock } = installStreams();
    const { result } = renderLive();
    await waitFor(() => expect(streams).toHaveLength(1));
    await act(async () => streams[0].push("event: revoked\ndata: {}\n\n"));
    await waitFor(() => expect(signOut).toHaveBeenCalledTimes(1));
    await vi.advanceTimersByTimeAsync(40000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(result.current.connected).toBe(false);
  });
});
