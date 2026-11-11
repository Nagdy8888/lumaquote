import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { SheetExport } from "./api";
import { ExportToolbar, sheetStatusText } from "./ExportToolbar";
import { renderWithClient } from "./testkit";

const request = vi.fn();
vi.mock("@/shared/api/client", () => ({
  request: (...args: unknown[]) => request(...args),
  downloadFile: vi.fn(),
}));
vi.mock("@/shared/auth/session", () => ({
  useSession: () => ({ session: { user: { id: "staff-1" } }, loading: false }),
}));

/** An export status with defaults for the fields a test does not care about. */
function exportView(overrides: Partial<SheetExport>): SheetExport {
  return {
    id: "e1",
    status: "queued",
    requested_at: "2026-11-08T08:00:00Z",
    completed_at: null,
    row_counts: null,
    error_code: null,
    ...overrides,
  };
}

beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }));
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("ExportToolbar", () => {
  /** Export queues, shows the Apps Script wait note, polls every 5 s and then shows row counts. */
  it("shows queued, then done with row counts", async () => {
    let latest = exportView({ id: null, status: "none", requested_at: null });
    request.mockImplementation((_path: string, init?: { method?: string }) => {
      if (init?.method === "POST") {
        latest = exportView({ status: "queued" });
        return Promise.resolve(latest);
      }
      return Promise.resolve(latest);
    });
    renderWithClient(<ExportToolbar />);
    const button = await screen.findByRole("button", {
      name: "Export to Google Sheets",
    });
    fireEvent.click(button);
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Queued. Apps Script picks it up within about a minute.",
    );
    expect(request).toHaveBeenCalledWith(
      "/inventory/sheet-exports",
      { method: "POST" },
      expect.any(String),
    );
    expect(button).toBeDisabled();
    latest = exportView({
      status: "done",
      completed_at: "2026-11-08T08:01:00Z",
      row_counts: { Stock: 12, "Customer Orders": 3, "Purchase Orders": 2 },
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5100);
    });
    const status = await screen.findByText(/Done/);
    expect(status).toHaveTextContent("Stock 12");
    expect(status).toHaveTextContent("Customer Orders 3");
    expect(status).toHaveTextContent("Purchase Orders 2");
  });
});

describe("sheetStatusText", () => {
  /** Failed exports name the short error code; a never-requested export says nothing. */
  it("describes failed and none", () => {
    expect(sheetStatusText(exportView({ status: "failed", error_code: "sheet_missing" }))).toBe(
      "Failed (sheet missing). You can export again.",
    );
    expect(sheetStatusText(exportView({ status: "none" }))).toBe("");
    expect(sheetStatusText(exportView({ status: "claimed" }))).toMatch(/writing/);
  });
});
