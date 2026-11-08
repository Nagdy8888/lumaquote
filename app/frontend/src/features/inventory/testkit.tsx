import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import type { OrderRow, StockRow } from "./api";

/**
 * Render a component inside a fresh query client (no retries) and a memory router, and return the
 * client so a test can spy on invalidation. Test-only helper; it never touches the network.
 */
export function renderWithClient(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  });
  const invalidate = vi.spyOn(client, "invalidateQueries");
  const view = render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
  return { ...view, client, invalidate };
}

/** A stock row with sensible defaults; override the fields a test cares about. */
export function stockRow(
  overrides: Partial<StockRow> = {},
): StockRow {
  return {
    product_id: "p1",
    sku: "LN-100",
    name: "Linear batten",
    family: "Linear",
    discontinued: false,
    on_hand: 100,
    reserved: 10,
    available: 90,
    reorder_level: 20,
    low: false,
    ...overrides,
  };
}

/** A pending customer order for conversation `c1` with one line. */
export function pendingOrder(
  overrides: Partial<OrderRow> = {},
): OrderRow {
  return {
    id: "o1",
    number: "ORD-1",
    conversation_id: "c1",
    quote_id: "q1",
    revision: 2,
    status: "pending",
    accepted_via: "telegram_button",
    accepted_at: "2026-11-08T08:00:00Z",
    confirmed_at: null,
    cancelled_at: null,
    cancel_reason: null,
    currency: "USD",
    total: "250.00",
    customer_name: "Synthetic customer",
    customer_company: "Fixture",
    created_at: "2026-11-08T08:00:00Z",
    lines: [
      {
        product_id: "p1",
        sku: "LN-100",
        name: "Linear batten",
        quantity: 5,
        unit_price: "50.00",
        line_total: "250.00",
      },
    ],
    ...overrides,
  };
}
