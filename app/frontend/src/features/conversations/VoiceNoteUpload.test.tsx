import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, expect, it, vi } from "vitest";
import { request } from "@/shared/api/client";
import { VoiceNoteUpload } from "./VoiceNoteUpload";

vi.mock("@/shared/api/client", () => ({ request: vi.fn() }));
afterEach(cleanup);

/** Preserve the original operation identity/version when the upload outcome is unknown, including background refresh. */
it("retries the same selected file without changing its operation precondition", /** Exercise the retry after a background version change without replacing its original identity. */ async function retrySelectedFile() {
  const client = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  });
  vi.mocked(request)
    .mockRejectedValueOnce(new Error("Network outcome uncertain."))
    .mockResolvedValueOnce({ status: "queued" });
  const view = render(
    <QueryClientProvider client={client}>
      <VoiceNoteUpload id="fixture" version={2} />
    </QueryClientProvider>,
  );
  const file = new File(["synthetic bytes"], "synthetic.wav", {
    type: "audio/wav",
  });
  fireEvent.change(screen.getByLabelText("Test customer voice note"), {
    target: { files: [file] },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Upload test voice note" }),
  );
  await screen.findByRole("alert");
  view.rerender(
    <QueryClientProvider client={client}>
      <VoiceNoteUpload id="fixture" version={9} />
    </QueryClientProvider>,
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Upload test voice note" }),
  );
  await waitFor(/** Wait for both explicit attempts to reach the API boundary. */ function confirmedUpload() {
    expect(request).toHaveBeenCalledTimes(2);
  });
  const calls = vi.mocked(request).mock.calls;
  expect(calls[0][2]).toBe(calls[1][2]);
  expect(calls[0][1]?.headers).toEqual(calls[1][1]?.headers);
  expect(calls[1][1]?.headers).toMatchObject({ "Expected-Version": "2" });
  await act(/** Finish the mutation reconciliation before disposing its query client. */ async function finishReconciliation() {
    await Promise.resolve();
  });
  client.clear();
});
