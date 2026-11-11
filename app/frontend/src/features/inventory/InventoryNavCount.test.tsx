import "@testing-library/jest-dom/vitest";
import { cleanup, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { InventoryNavCount } from "./InventoryNavCount";
import { renderWithClient } from "./testkit";

const request = vi.fn();
vi.mock("@/shared/api/client", () => ({
  request: (...args: unknown[]) => request(...args),
  downloadFile: vi.fn(),
}));
vi.mock("@/shared/auth/session", () => ({
  useSession: () => ({ session: { user: { id: "staff-1" } }, loading: false }),
}));
afterEach(cleanup);

/** An alerts payload whose counts are the given numbers (lists are not read by the badge). */
function alerts(shortage: number, refused: number, low: number) {
  return {
    alerts: [],
    low_stock: [],
    counts: {
      shortage,
      acceptance_refused: refused,
      low_stock: low,
      total: shortage + refused + low,
    },
  };
}

describe("InventoryNavCount", () => {
  /** The badge is the server's total: open alerts plus low-stock products. */
  it("shows open alerts plus low-stock products", async () => {
    request.mockResolvedValue(alerts(1, 1, 3));
    renderWithClient(<InventoryNavCount />);
    expect(await screen.findByLabelText("5 open stock items")).toHaveTextContent("5");
  });

  /** Zero open items renders nothing, not a zero badge. */
  it("renders nothing at zero", async () => {
    request.mockResolvedValue(alerts(0, 0, 0));
    const { container } = renderWithClient(<InventoryNavCount />);
    await waitFor(() => expect(request).toHaveBeenCalledWith("/inventory/alerts", expect.anything()));
    expect(container).toBeEmptyDOMElement();
  });
});
