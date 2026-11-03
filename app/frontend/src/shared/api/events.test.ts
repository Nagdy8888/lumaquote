import { describe, expect, it, vi, afterEach } from "vitest";
import { ApiError } from "./client";
import { openEventStream, parseEventStream } from "./events";

vi.mock("../auth/client", () => ({ auth: {} }));
afterEach(vi.unstubAllGlobals);

/** Build a streaming Response from chunks so reads happen in controlled pieces. */
function streamOf(chunks: string[], init: ResponseInit = {}) {
  const encoder = new TextEncoder();
  return new Response(
    new ReadableStream({
      /** Enqueue every chunk then close, so the body reads in controlled pieces. */
      start(controller) {
        for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
        controller.close();
      },
    }),
    init,
  );
}

describe("parseEventStream", () => {
  /** A complete event is returned and nothing is left over. */
  it("parses one event with LF endings", () => {
    expect(
      parseEventStream('event: refresh\ndata: {"revision": 4}\n\n', ""),
    ).toEqual({
      events: [{ event: "refresh", data: '{"revision": 4}' }],
      rest: "",
    });
  });

  /** An event split across chunks stays buffered until its blank line arrives. */
  it("holds a partial event until the next chunk completes it", () => {
    const first = parseEventStream("event: refresh\nda", "");
    expect(first).toEqual({ events: [], rest: "event: refresh\nda" });
    const second = parseEventStream('ta: {"revision": 5}\n\n', first.rest);
    expect(second.events).toEqual([
      { event: "refresh", data: '{"revision": 5}' },
    ]);
    expect(second.rest).toBe("");
  });

  /** Two events in one chunk are both returned, and a trailing partial is kept. */
  it("returns several events from one chunk", () => {
    const parsed = parseEventStream(
      "event: refresh\ndata: 1\n\nevent: revoked\ndata: {}\n\nevent: refr",
      "",
    );
    expect(parsed.events).toEqual([
      { event: "refresh", data: "1" },
      { event: "revoked", data: "{}" },
    ]);
    expect(parsed.rest).toBe("event: refr");
  });

  /** CRLF endings, including a CR/LF pair split across chunks, parse like LF. */
  it("handles CRLF line endings and a split CRLF pair", () => {
    expect(
      parseEventStream("event: refresh\r\ndata: 7\r\n\r\n", "").events,
    ).toEqual([{ event: "refresh", data: "7" }]);
    const first = parseEventStream("event: refresh\r\ndata: 8\r\n\r", "");
    expect(first.events).toEqual([]);
    const second = parseEventStream("\n", first.rest);
    expect(second.events).toEqual([{ event: "refresh", data: "8" }]);
  });

  /** Comment lines (keep-alives) never become events, even alone in a block. */
  it("ignores comment lines", () => {
    const parsed = parseEventStream(
      ": keep-alive\n\n: note\nevent: refresh\ndata: 9\n\n",
      "",
    );
    expect(parsed.events).toEqual([{ event: "refresh", data: "9" }]);
  });

  /** Several data lines are joined with a newline and the event name defaults. */
  it("joins data lines and defaults the event name", () => {
    expect(parseEventStream("data: a\ndata: b\n\n", "").events).toEqual([
      { event: "message", data: "a\nb" },
    ]);
  });
});

describe("openEventStream", () => {
  /** The bearer header is sent, events arrive in order across split reads, and onOpen fires once. */
  it("sends the bearer header and delivers events", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        streamOf(['event: refresh\ndata: {"revi', 'sion": 1}\n\n']),
      );
    vi.stubGlobal("fetch", fetchMock);
    const events: unknown[] = [];
    const onOpen = vi.fn();
    await openEventStream({
      path: "/events",
      token: "secret-token",
      signal: new AbortController().signal,
      onEvent: (event) => events.push(event),
      onOpen,
    });
    expect(events).toEqual([{ event: "refresh", data: '{"revision": 1}' }]);
    expect(onOpen).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/events");
    expect(init.headers).toMatchObject({
      Authorization: "Bearer secret-token",
      Accept: "text/event-stream",
    });
  });

  /** A non-2xx answer rejects with the status and a fixed message that never echoes the token. */
  it("rejects with ApiError on a non-2xx response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("nope", { status: 401 })),
    );
    const failure = await openEventStream({
      path: "/events",
      token: "secret-token",
      signal: new AbortController().signal,
      onEvent: vi.fn(),
    }).catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(ApiError);
    expect((failure as ApiError).status).toBe(401);
    expect((failure as ApiError).message).not.toContain("secret-token");
  });
});
