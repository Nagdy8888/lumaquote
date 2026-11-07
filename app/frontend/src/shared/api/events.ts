import { ApiError } from "./client";

/** One server-sent event: its name (default "message") and the joined data lines. */
export type StreamEvent = { event: string; data: string };

/**
 * Split buffered server-sent-event text into complete events.
 * Inputs: the next decoded `chunk` and the unfinished `buffer` returned by the
 * previous call. Output: complete events (blocks ended by a blank line) and the
 * unfinished remainder to pass back next time. Handles CRLF, LF and a CR/LF pair
 * split across chunks, ignores comment lines (starting with ":") and joins
 * several `data:` lines with a newline. Pure: no I/O, never logs event data.
 */
export function parseEventStream(
  chunk: string,
  buffer: string,
): { events: StreamEvent[]; rest: string } {
  const joined = buffer + chunk;
  // A trailing CR may be the first half of a CRLF pair; keep it for the next chunk.
  const held = joined.endsWith("\r") ? "\r" : "";
  const text = joined
    .slice(0, joined.length - held.length)
    .replace(/\r\n?/g, "\n");
  const blocks = text.split("\n\n");
  const rest = (blocks.pop() ?? "") + held;
  const events: StreamEvent[] = [];
  for (const block of blocks) {
    let event = "message";
    const data: string[] = [];
    let seen = false;
    for (const line of block.split("\n")) {
      if (line === "" || line.startsWith(":")) continue;
      const colon = line.indexOf(":");
      const field = colon === -1 ? line : line.slice(0, colon);
      let value = colon === -1 ? "" : line.slice(colon + 1);
      if (value.startsWith(" ")) value = value.slice(1);
      if (field === "event") {
        event = value;
        seen = true;
      } else if (field === "data") {
        data.push(value);
        seen = true;
      }
    }
    if (seen) events.push({ event, data: data.join("\n") });
  }
  return { events, rest };
}

/**
 * Open an authenticated server-sent-event stream and deliver each event.
 * Inputs: same-origin API `path` (without the `/api` prefix), the staff bearer
 * `token`, an `AbortSignal` that ends the read, `onEvent` for every complete event
 * and an optional `onOpen` called once when the server accepts the stream.
 * Output: resolves when the server ends the stream or the signal aborts.
 * Side effects: one HTTP request; `EventSource` is not used because it cannot send
 * the bearer header. Authority: the token is sent only to the same-origin API and
 * is never logged; event data is passed to `onEvent` and never logged here.
 * Errors: a non-2xx answer or a missing body rejects with `ApiError` carrying the
 * status and a fixed message (no response content).
 */
export async function openEventStream({
  path,
  token,
  signal,
  onEvent,
  onOpen,
}: {
  path: string;
  token: string;
  signal: AbortSignal;
  onEvent: (event: StreamEvent) => void;
  onOpen?: () => void;
}): Promise<void> {
  const response = await fetch(`/api${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "text/event-stream",
    },
    signal,
  });
  if (!response.ok || !response.body)
    throw new ApiError(
      "The live update stream could not be opened.",
      response.status,
    );
  onOpen?.();
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    const parsed = parseEventStream(
      decoder.decode(value, { stream: true }),
      buffer,
    );
    buffer = parsed.rest;
    for (const event of parsed.events) onEvent(event);
  }
}
