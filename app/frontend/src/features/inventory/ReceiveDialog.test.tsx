import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { PurchaseOrderRow } from "./api";
import { ReceiveDialog, receiptQuantity } from "./ReceiveDialog";
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

const order: PurchaseOrderRow = {
  id: "po1",
  number: "PO-7",
  supplier: "Acme Lighting",
  status: "partially_received",
  expected_on: null,
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
      quantity_received: 6,
      unit_cost: "12.50",
    },
    {
      product_id: "p2",
      sku: "HB-200",
      name: "High bay",
      quantity_ordered: 4,
      quantity_received: 4,
      unit_cost: "40.00",
    },
  ],
};

describe("receiptQuantity", () => {
  /** Pure rule: empty is zero, whole numbers up to the outstanding quantity pass, others fail. */
  it("accepts up to the remaining quantity only", () => {
    expect(receiptQuantity("", 4)).toEqual({ quantity: 0, error: null });
    expect(receiptQuantity("4", 4)).toEqual({ quantity: 4, error: null });
    expect(receiptQuantity("5", 4).error).toMatch(/Cannot exceed the 4/);
    expect(receiptQuantity("1.5", 4).error).toMatch(/whole number/);
    expect(receiptQuantity("-1", 4).error).toMatch(/whole number/);
  });
});

describe("ReceiveDialog", () => {
  /** A fully received line is not offered; typing more than remaining blocks the button. */
  it("refuses more than the quantity still outstanding", () => {
    renderWithClient(<ReceiveDialog order={order} onClose={vi.fn()} />);
    expect(screen.queryByLabelText(/HB-200/)).toBeNull();
    const input = screen.getByLabelText(/LN-100/);
    const submit = screen.getByRole("button", { name: "Receive goods" });
    expect(submit).toBeDisabled();
    fireEvent.change(input, { target: { value: "5" } });
    expect(screen.getByText(/Cannot exceed the 4 still outstanding/)).toBeInTheDocument();
    expect(submit).toBeDisabled();
    expect(request).not.toHaveBeenCalled();
  });

  /** A partial quantity within the limit is sent with an idempotency key, only for lines that have one. */
  it("sends a partial receipt", async () => {
    request.mockResolvedValue(order);
    const onClose = vi.fn();
    renderWithClient(<ReceiveDialog order={order} onClose={onClose} />);
    fireEvent.change(screen.getByLabelText(/LN-100/), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "Receive goods" }));
    await waitFor(() =>
      expect(request).toHaveBeenCalledWith(
        "/purchase-orders/po1/receive",
        {
          method: "POST",
          body: JSON.stringify({ lines: [{ product_id: "p1", quantity: 3 }] }),
        },
        expect.any(String),
      ),
    );
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });
});
