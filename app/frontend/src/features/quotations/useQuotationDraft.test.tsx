import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { ConversationDetail } from "@/shared/api/types";
import { useQuotationDraft } from "./useQuotationDraft";

/** Construct complete read-contract fixtures without mocking the local edit/reconciliation behavior under test. */
function fixture(version = 1, revision = 1, quantity = 3): ConversationDetail {
  const time = "2026-10-29T08:00:00Z";
  return {
    conversation: {
      id: "conversation",
      company_id: "company",
      customer_name: "Synthetic customer",
      customer_company: "Fixture",
      recipient: "local:customer",
      channel: "local_test",
      owner: "agent",
      status: "review",
      version,
      created_at: time,
      updated_at: time,
      last_customer_at: time,
    },
    messages: [],
    delivery: [],
    quote: {
      id: `quote-${revision}`,
      conversation_id: "conversation",
      number: "LQ-FIXTURE",
      revision,
      status: "review",
      created_at: time,
      valid_until: "2026-11-05T08:00:00Z",
      content: {
        lines: [
          {
            product_id: "product",
            sku: "DL-001",
            name: "Fixture luminaire",
            quantity,
            unit: "each",
            unit_price: "32.00",
            line_total: "96.00",
            source_id: "source",
            page: 1,
          },
        ],
        currency: "USD",
        tax: "Excluded",
        subtotal: "96.00",
        discount_percent: "0",
        discount: "0.00",
        shipping: "0.00",
        total: "96.00",
        terms: "Staff confirmation required.",
        stock_reserved: false,
        customer_name: "Synthetic customer",
        customer_company: "Fixture",
      },
    },
  };
}

/** Remove hook instances so no local draft state persists into another regression scenario. */
function cleanHooks() {
  cleanup();
}
afterEach(cleanHooks);

/** Group business-relevant local draft synchronization and conflict cases. */
function draftSuite() {
  /** Preserve a salesperson's unsaved quantity when another revision is received, retaining its original version precondition. */
  function preservesConflict() {
    const { result, rerender } = renderHook(
      ({ detail }) => useQuotationDraft(detail),
      { initialProps: { detail: fixture() } },
    );
    act(() =>
      result.current.updateLines([{ product_id: "product", quantity: 4 }]),
    );
    rerender({ detail: fixture(8, 2, 9) });
    expect(result.current.lines[0].quantity).toBe(4);
    expect(result.current.baseVersion).toBe(1);
    expect(result.current.conflict).toBe(true);
    act(() => result.current.discardEdits());
    expect(result.current.lines[0].quantity).toBe(9);
    expect(result.current.dirty).toBe(false);
    expect(result.current.conflict).toBe(false);
  }
  it(
    "preserves unsaved edits and detects a newer server revision",
    preservesConflict,
  );

  /** Capture the version at the first edit, including changes that arrived while the form was clean. */
  function capturesLatestCleanVersion() {
    const { result, rerender } = renderHook(
      ({ detail }) => useQuotationDraft(detail),
      { initialProps: { detail: fixture() } },
    );
    rerender({ detail: fixture(6) });
    act(() => result.current.updateShipping("12.00"));
    expect(result.current.baseVersion).toBe(6);
    expect(result.current.conflict).toBe(false);
  }
  it(
    "uses the authoritative version observed when editing starts",
    capturesLatestCleanVersion,
  );
}
describe("Quotation draft concurrency", draftSuite);
