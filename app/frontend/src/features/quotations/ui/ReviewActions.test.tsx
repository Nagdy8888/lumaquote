import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ConversationDetail } from "@/shared/api/types";
import { ReviewActions } from "./ReviewActions";

vi.mock("@/shared/ui/document-button", () => ({ DocumentButton: () => null }));
afterEach(cleanup);

/** Build a quote under review whose server total string is distinct from any sum of lines. */
function detail(
  revision = 2,
  id = "quote-1",
  owner = "agent",
): ConversationDetail {
  const time = "2026-10-29T08:00:00Z";
  return {
    conversation: {
      id: "conversation",
      company_id: "company",
      customer_name: "Synthetic customer",
      customer_company: "Fixture",
      recipient: "local:customer",
      channel: "local_test",
      owner,
      status: "review",
      version: 1,
      created_at: time,
      updated_at: time,
      last_customer_at: time,
    },
    messages: [],
    delivery: [],
    quote: {
      id,
      conversation_id: "conversation",
      number: "LQ-FIXTURE",
      revision,
      status: "review",
      created_at: time,
      valid_until: "2026-11-05T08:00:00Z",
      content: {
        lines: [],
        currency: "USD",
        tax: "Excluded",
        subtotal: "1.00",
        discount_percent: "0",
        discount: "0.00",
        shipping: "0.00",
        total: "1234.56",
        terms: "Staff confirmation required.",
        stock_reserved: false,
        customer_name: "Synthetic customer",
        customer_company: "Fixture",
      },
    },
  } as ConversationDetail;
}

/** Render the actions with a spy decision handler and optional capture mode; `change` swaps the displayed detail. */
function view(d: ConversationDetail, onDecide = vi.fn(), capture = false) {
  /** Build the element for one detail so rerender keeps the same props otherwise. */
  const ui = (next: ConversationDetail) => (
    <ReviewActions
      detail={next}
      dirty={false}
      hasLines
      pending={false}
      capture={capture}
      onSave={vi.fn()}
      onDecide={onDecide}
    />
  );
  const result = render(ui(d));
  return {
    ...result,
    onDecide,
    change: (next: ConversationDetail) => result.rerender(ui(next)),
  };
}

describe("ReviewActions approval confirmation", () => {
  /** Step 1 alone never approves; step 2 restates the server total string and the revision. */
  it("restates the server total and calls approve once", () => {
    const { onDecide } = view(detail());
    fireEvent.click(screen.getByRole("button", { name: "Review approval" }));
    expect(onDecide).not.toHaveBeenCalled();
    const panel = screen.getByRole("region", { name: "Confirm approval" });
    expect(panel).toHaveTextContent("$1,234.56");
    expect(panel).toHaveTextContent("LQ-FIXTURE");
    expect(panel).toHaveTextContent("Synthetic customer");
    expect(panel).toHaveTextContent("the local test channel");
    fireEvent.click(
      screen.getByRole("button", {
        name: "Approve revision 2 & queue delivery",
      }),
    );
    expect(onDecide).toHaveBeenCalledTimes(1);
    expect(onDecide).toHaveBeenCalledWith("approve");
  });

  /** Capture mode never shows the customer name in the panel. */
  it("says this customer in capture mode", () => {
    view(detail(), vi.fn(), true);
    fireEvent.click(screen.getByRole("button", { name: "Review approval" }));
    const panel = screen.getByRole("region", { name: "Confirm approval" });
    expect(panel).toHaveTextContent("this customer");
    expect(panel).not.toHaveTextContent("Synthetic customer");
  });

  /** A changed revision closes the panel, says so, and does not call onDecide. */
  it("closes when the displayed revision changes", () => {
    const { onDecide, change } = view(detail(2));
    fireEvent.click(screen.getByRole("button", { name: "Review approval" }));
    change(detail(3));
    expect(
      screen.queryByRole("region", { name: "Confirm approval" }),
    ).toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent(
      "This quotation changed. Review the new revision.",
    );
    expect(
      screen.getByRole("button", { name: "Review approval" }),
    ).toBeEnabled();
    expect(onDecide).not.toHaveBeenCalled();
  });

  /** A different quote id with the same revision number also closes the panel. */
  it("closes when the quote id changes", () => {
    const { change } = view(detail(2, "quote-1"));
    fireEvent.click(screen.getByRole("button", { name: "Review approval" }));
    change(detail(2, "quote-2"));
    expect(
      screen.queryByRole("region", { name: "Confirm approval" }),
    ).toBeNull();
  });

  /** Cancel closes without a call and returns focus to Review approval; opening moves focus to the heading. */
  it("moves focus on open and returns it on Cancel", () => {
    const { onDecide } = view(detail());
    fireEvent.click(screen.getByRole("button", { name: "Review approval" }));
    expect(
      screen.getByRole("heading", { name: "Confirm approval" }),
    ).toHaveFocus();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(
      screen.queryByRole("region", { name: "Confirm approval" }),
    ).toBeNull();
    expect(
      screen.getByRole("button", { name: "Review approval" }),
    ).toHaveFocus();
    expect(onDecide).not.toHaveBeenCalled();
  });

  /** Escape closes the panel without a decision. */
  it("closes on Escape", () => {
    const { onDecide } = view(detail());
    fireEvent.click(screen.getByRole("button", { name: "Review approval" }));
    fireEvent.keyDown(
      screen.getByRole("heading", { name: "Confirm approval" }),
      { key: "Escape" },
    );
    expect(
      screen.queryByRole("region", { name: "Confirm approval" }),
    ).toBeNull();
    expect(
      screen.getByRole("button", { name: "Review approval" }),
    ).toHaveFocus();
    expect(onDecide).not.toHaveBeenCalled();
  });

  /** When staff owns the conversation, step 1 is disabled so approval cannot start. */
  it("disables Review approval while staff owns the conversation", () => {
    view(detail(2, "quote-1", "staff"));
    expect(
      screen.getByRole("button", { name: "Review approval" }),
    ).toBeDisabled();
  });

  /** Request changes still works from the first step and does not require the panel. */
  it("keeps Request changes available", () => {
    const { onDecide } = view(detail());
    fireEvent.click(screen.getByRole("button", { name: "Request changes" }));
    expect(onDecide).toHaveBeenCalledWith("reject");
  });
});
