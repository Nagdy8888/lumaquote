import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { lineIsValid } from "./NewPurchaseOrderDialog";
import { PurchaseOrdersTab } from "./PurchaseOrdersTab";
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

const purchase = {
  id: "po1",
  number: "PO-7",
  supplier: "Acme Lighting",
  status: "ordered",
  expected_on: "2026-12-01",
  notes: null,
  created_by: "u1",
  created_at: "2026-11-08T08:00:00Z",
  updated_at: "2026-11-08T08:00:00Z",
  lines: [
    {
      product_id: "p1",
      sku: "LN-100",
      name: "Linear batten",
      quantity_ordered: 10,
      quantity_received: 0,
      unit_cost: "12.50",
    },
  ],
};

describe("PurchaseOrdersTab", () => {
  /** A salesperson reads the orders but sees no create, receive or cancel control. */
  it("hides purchasing controls from a salesperson", async () => {
    request.mockResolvedValue({ items: [purchase] });
    renderWithClient(<PurchaseOrdersTab isAdmin={false} />);
    expect(await screen.findByText("PO-7")).toBeInTheDocument();
    expect(screen.getByText("Ordered")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "New purchase order" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Receive goods" })).toBeNull();
    expect(screen.queryByRole("button", { name: /Cancel purchase order/ })).toBeNull();
  });

  /** An administrator sees all three controls; cancelling sends an idempotency key. */
  it("shows purchasing controls to an administrator", async () => {
    request.mockResolvedValue({ items: [purchase] });
    renderWithClient(<PurchaseOrdersTab isAdmin />);
    expect(await screen.findByRole("button", { name: "New purchase order" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Receive goods" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Cancel purchase order" }));
    await waitFor(() =>
      expect(request).toHaveBeenCalledWith(
        "/purchase-orders/po1/cancel",
        { method: "POST" },
        expect.any(String),
      ),
    );
  });
});

describe("lineIsValid", () => {
  /** A line needs a product, a whole quantity 1 to 100000 and a cost with at most two decimals. */
  it("enforces the API bounds", () => {
    const ok = { id: 1, product: "p1", quantity: "5", cost: "12.50" };
    expect(lineIsValid(ok)).toBe(true);
    expect(lineIsValid({ ...ok, product: "" })).toBe(false);
    expect(lineIsValid({ ...ok, quantity: "0" })).toBe(false);
    expect(lineIsValid({ ...ok, quantity: "100001" })).toBe(false);
    expect(lineIsValid({ ...ok, cost: "12.345" })).toBe(false);
    expect(lineIsValid({ ...ok, cost: "" })).toBe(false);
  });
});
