import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StockTable } from "./StockTable";
import { stockRow } from "./testkit";

afterEach(cleanup);

const items = [
  stockRow({ product_id: "a", sku: "LN-100", name: "Linear batten" }),
  stockRow({
    product_id: "b",
    sku: "HB-200",
    name: "High bay",
    family: "High bay",
    on_hand: 25,
    reserved: 5,
    available: 20,
    low: true,
  }),
  stockRow({
    product_id: "c",
    sku: "TR-300",
    name: "Track spot",
    family: "Track",
    on_hand: 0,
    reserved: 0,
    available: 0,
    low: true,
  }),
];

/** Render the table with spy callbacks; `isAdmin` toggles the admin-only row actions. */
function view(isAdmin: boolean) {
  const handlers = { onAdjust: vi.fn(), onReorder: vi.fn(), onHistory: vi.fn() };
  render(<StockTable items={items} isAdmin={isAdmin} {...handlers} />);
  return handlers;
}

describe("StockTable", () => {
  /** Every row shows its numbers and a text status chip: OK, Low or Out. */
  it("renders rows with OK, Low and Out chips", () => {
    view(false);
    const rows = screen.getAllByRole("row");
    expect(rows).toHaveLength(4); // header + 3 products
    const linear = within(rows[1]);
    expect(linear.getByText("LN-100")).toBeInTheDocument();
    expect(linear.getByText("90")).toBeInTheDocument();
    expect(linear.getByText("OK")).toBeInTheDocument();
    expect(within(rows[2]).getByText("Low")).toBeInTheDocument();
    expect(within(rows[3]).getByText("Out")).toBeInTheDocument();
  });

  /** A salesperson never sees Adjust or Reorder level, but can still open the history. */
  it("hides admin controls for a salesperson", () => {
    view(false);
    expect(screen.queryByRole("button", { name: /Adjust stock/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Set reorder level/ })).toBeNull();
    expect(
      screen.getAllByRole("button", { name: /Movement history/ }),
    ).toHaveLength(3);
  });

  /** An administrator sees both controls on every row and they call back with that row. */
  it("shows admin controls for an administrator", () => {
    const handlers = view(true);
    fireEvent.click(screen.getByRole("button", { name: "Adjust stock for HB-200" }));
    expect(handlers.onAdjust).toHaveBeenCalledWith(items[1]);
    fireEvent.click(
      screen.getByRole("button", { name: "Set reorder level for TR-300" }),
    );
    expect(handlers.onReorder).toHaveBeenCalledWith(items[2]);
  });

  /** Text search and the status filter narrow the rows without changing any number. */
  it("filters by text and by status", () => {
    view(true);
    fireEvent.change(screen.getByLabelText(/Search stock/), {
      target: { value: "track" },
    });
    expect(screen.getAllByRole("row")).toHaveLength(2);
    expect(screen.getByText("TR-300")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Search stock/), {
      target: { value: "" },
    });
    fireEvent.change(screen.getByLabelText("Filter by stock status"), {
      target: { value: "low" },
    });
    expect(screen.getAllByRole("row")).toHaveLength(2);
    expect(screen.getByText("HB-200")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("1 of 3 products");
  });
});
