import "@testing-library/jest-dom/vitest";
import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MovementsDrawer } from "./MovementsDrawer";
import { renderWithClient, stockRow } from "./testkit";

const request = vi.fn();
vi.mock("@/shared/api/client", () => ({
  request: (...args: unknown[]) => request(...args),
  downloadFile: vi.fn(),
}));
vi.mock("@/shared/auth/session", () => ({
  useSession: () => ({ session: { user: { id: "staff-1" } }, loading: false }),
}));
afterEach(cleanup);

const base = {
  product_id: "p1",
  sku: "LN-100",
  name: "Linear batten",
  reference_id: null,
  reason: null,
  actor: "u1",
  created_at: "2026-11-08T08:00:00Z",
};

describe("MovementsDrawer", () => {
  /** A receipt names its purchase order and an order movement its order; an adjustment shows no number. */
  it("shows the PO or SO number next to the movement kind", async () => {
    request.mockResolvedValue({
      items: [
        { ...base, id: "m1", delta: 10, kind: "receipt", reference_id: "po1", reference: "PO-0007" },
        { ...base, id: "m2", delta: -3, kind: "order", reference_id: "o1", reference: "SO-0002" },
        { ...base, id: "m3", delta: 1, kind: "adjustment", reference: null, reason: "Recount" },
      ],
      next: null,
    });
    renderWithClient(<MovementsDrawer row={stockRow()} onClose={() => {}} />);
    expect(await screen.findByText("Supplier receipt · PO-0007")).toBeInTheDocument();
    expect(screen.getByText("Customer order · SO-0002")).toBeInTheDocument();
    expect(screen.getByText("Manual adjustment")).toBeInTheDocument();
  });
});
