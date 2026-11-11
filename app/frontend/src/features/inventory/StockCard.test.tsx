import "@testing-library/jest-dom/vitest";
import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StockCard } from "./StockCard";
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

describe("StockCard", () => {
  /** Six out-of-stock products and no stored alerts: the card shows the badge total, not a zero. */
  it("shows the same open-alert number as the navigation badge", async () => {
    request.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/inventory/alerts")
          ? {
              alerts: [],
              low_stock: [],
              counts: { shortage: 0, acceptance_refused: 0, low_stock: 6, total: 6 },
            }
          : { items: [] },
      ),
    );
    renderWithClient(<StockCard />);
    expect(await screen.findAllByText("06")).toHaveLength(2);
    expect(screen.getByText("Low / out of stock")).toBeInTheDocument();
    expect(screen.getByText("Open alerts").nextSibling).toHaveTextContent("06");
    expect(screen.getByText("Orders to confirm").nextSibling).toHaveTextContent("00");
  });
});
