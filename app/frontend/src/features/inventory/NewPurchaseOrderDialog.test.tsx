import "@testing-library/jest-dom/vitest";
import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NewPurchaseOrderDialog } from "./NewPurchaseOrderDialog";
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

describe("NewPurchaseOrderDialog", () => {
  /** Discontinued products stay out of the picker and the dialog says so. */
  it("explains that discontinued products are not listed", async () => {
    request.mockResolvedValue({
      items: [
        stockRow({ product_id: "a", sku: "LN-100" }),
        stockRow({ product_id: "b", sku: "LN-012", discontinued: true }),
      ],
    });
    renderWithClient(<NewPurchaseOrderDialog open onClose={() => {}} />);
    expect(await screen.findByText("Discontinued products are not listed.")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /LN-100/ })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: /LN-012/ })).toBeNull();
  });

  /** With nothing discontinued the hint is not shown. */
  it("shows no hint when every product can be ordered", async () => {
    request.mockResolvedValue({ items: [stockRow({ product_id: "a", sku: "LN-100" })] });
    renderWithClient(<NewPurchaseOrderDialog open onClose={() => {}} />);
    expect(await screen.findByRole("option", { name: /LN-100/ })).toBeInTheDocument();
    expect(screen.queryByText("Discontinued products are not listed.")).toBeNull();
  });
});
