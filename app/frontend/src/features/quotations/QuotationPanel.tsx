import "./quotations.css";

import { ChevronDown, FileCheck2 } from "lucide-react";
import type { ConversationDetail, Product } from "@/shared/api/types";
import { useWorkspaceContext } from "@/shared/api/workspace-context";
import { useConversationAction } from "@/features/conversations/api";
import { OrderBanner } from "@/features/inventory/OrderBanner";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Status } from "@/shared/ui/status";

import { useQuotationDraft } from "./useQuotationDraft";
import { ProductSelections } from "./ui/ProductSelections";
import { QuoteSummary } from "./ui/QuoteSummary";
import { ReviewActions } from "./ui/ReviewActions";

/**
 * Edit product selections and review server-calculated quotations; approval never uses a browser-calculated total.
 * When the customer accepted the quotation, a banner above the quote offers Confirm order and Cancel order.
 */
export function QuotationPanel({
  detail,
  products,
  role,
}: {
  detail: ConversationDetail;
  products: Product[];
  role: string;
}) {
  const { capture } = useWorkspaceContext();
  const { conversation, quote } = detail;
  const delivery = detail.delivery.filter((item) => item.kind === "quotation");
  const draft = useQuotationDraft(detail);
  const { lines, discount, shipping, dirty } = draft;
  const action = useConversationAction(conversation.id);
  /** Persist selected products as a new immutable revision; the currently displayed conversation version detects conflicts. */
  function saveDraft() {
    action.mutate(
      {
        action: "draft",
        body: {
          expected_version: dirty ? draft.baseVersion : conversation.version,
          lines,
          discount_percent: discount,
          shipping,
          terms:
            quote?.content.terms ??
            "Delivery date subject to staff confirmation.",
        },
        key: crypto.randomUUID(),
      },
      { onSuccess: draft.markSaved },
    );
  }
  /** Submit the exact displayed revision for authorized approval or rejection; the outbox handles delivery separately. */
  function decide(decision: "approve" | "reject") {
    if (quote)
      action.mutate({
        action: "decision",
        body: { expected_revision: quote.revision, decision },
        key: crypto.randomUUID(),
      });
  }
  /** Explicitly discard local fields and clear a prior conflict after loading the current canonical revision. */
  function discardLocalEdits() {
    draft.discardEdits();
    action.reset();
  }
  return (
    <aside
      className="quotation-panel"
      aria-label="Quotation editing and approval"
    >
      <header>
        <div>
          <FileCheck2 />
          <h2>Quotation workspace</h2>
        </div>
        <span>{quote ? `Revision ${quote.revision}` : "New draft"}</span>
      </header>
      <div className="quotation-panel-body">
        <OrderBanner
          conversationId={conversation.id}
          quoteNumber={quote?.number ?? null}
        />
        <div className="quote-context">
          <h3>{quote?.number ?? "Make the brief a proposal."}</h3>
          <p>
            {quote
              ? "Review the exact products and commercial terms."
              : "Select products from the catalog to prepare a quotation for review."}
          </p>
          {quote && <Status value={quote.status} />}
        </div>
        {draft.conflict && (
          <div role="alert" className="unsaved-note">
            This request changed while you were editing. Your local entries are
            preserved. Save will require a fresh version.
            <Button type="button" variant="outline" onClick={discardLocalEdits}>
              Discard local edits & load latest
            </Button>
          </div>
        )}
        <ProductSelections
          lines={lines}
          products={products}
          onChange={draft.updateLines}
        />

        <details className="commercial-adjustments">
          <summary>
            Commercial adjustments
            <ChevronDown />
          </summary>
          <div>
            <label>
              Discount %
              <Input
                type="number"
                min="0"
                max="10"
                step="0.01"
                value={discount}
                disabled={role !== "admin"}
                onChange={(event) => {
                  draft.updateDiscount(event.target.value);
                }}
              />
            </label>
            <label>
              Shipping USD
              <Input
                type="number"
                min="0"
                max="10000"
                step="0.01"
                value={shipping}
                onChange={(event) => {
                  draft.updateShipping(event.target.value);
                }}
              />
            </label>
          </div>
          <small>Discounts require administrator access.</small>
        </details>
        <QuoteSummary quote={quote} dirty={dirty} />

        {delivery[0] && (
          <div className="delivery-summary">
            <span>Latest delivery</span>
            <Status value={delivery[0].status} />
            {delivery[0].error_code && (
              <small>{delivery[0].error_code.replaceAll("_", " ")}</small>
            )}
          </div>
        )}
        {action.isError && (
          <p className="error-text" role="alert">
            {action.error.message}
          </p>
        )}
      </div>
      <ReviewActions
        detail={detail}
        dirty={dirty}
        hasLines={lines.length > 0}
        pending={action.isPending}
        capture={capture}
        onSave={saveDraft}
        onDecide={decide}
      />
    </aside>
  );
}
