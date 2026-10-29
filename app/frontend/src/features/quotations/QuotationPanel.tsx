import "./quotations.css";
import { useState } from "react";
import {
  BookOpenCheck,
  Check,
  ChevronDown,
  FileCheck2,
  Plus,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import type { ConversationDetail, Product } from "@/shared/api/types";
import { useWorkspaceContext } from "@/shared/api/workspace-context";
import { useConversationAction } from "@/features/conversations/api";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Status, money } from "@/shared/ui/status";
import { DocumentButton } from "@/shared/ui/document-button";

type Line = { product_id: string; quantity: number };

/** Edit product selections and review server-calculated quotations; approval never uses a browser-calculated total. */
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
  const { conversation, quote, delivery } = detail;
  const [lines, setLines] = useState<Line[]>(
    quote?.content.lines.map((line) => ({
      product_id: line.product_id,
      quantity: line.quantity,
    })) ?? [],
  );
  const [selected, setSelected] = useState("");
  const [dirty, setDirty] = useState(false);
  const [discount, setDiscount] = useState(
    quote?.content.discount_percent ?? "0",
  );
  const [shipping, setShipping] = useState(quote?.content.shipping ?? "0");
  const action = useConversationAction(conversation.id);
  const available = products.filter(
    (p) =>
      !p.discontinued &&
      p.available > 0 &&
      !lines.some((line) => line.product_id === p.id),
  );
  /** Add a selected catalog product using its required pack size; the server revalidates stock before saving. */
  function addProduct() {
    const p = products.find((product) => product.id === selected);
    if (p) {
      setLines([...lines, { product_id: p.id, quantity: p.pack_size }]);
      setSelected("");
      setDirty(true);
    }
  }
  /** Persist selected products as a new immutable revision; the currently displayed conversation version detects conflicts. */
  function saveDraft() {
    action.mutate({
      action: "draft",
      body: {
        expected_version: conversation.version,
        lines,
        discount_percent: discount,
        shipping,
        terms:
          quote?.content.terms ??
          "Delivery date subject to staff confirmation.",
      },
      key: crypto.randomUUID(),
    });
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
  return (
    <aside className="quotation-panel" aria-label="Quotation editing and approval">
      <header>
        <div>
          <FileCheck2 />
          <h2>Quotation workspace</h2>
        </div>
        <span>{quote ? `Revision ${quote.revision}` : "New draft"}</span>
      </header>
      <div className="quotation-panel-body">
        <div className="quote-context">
          <h3>{quote?.number ?? "Make the brief a proposal."}</h3>
          <p>
            {quote
              ? "Review the exact products and commercial terms."
              : "Select products from the catalog to prepare a quotation for review."}
          </p>
          {quote && <Status value={quote.status} />}
        </div>
        <div className="quote-lines">
          {lines.map((line, index) => {
            const p = products.find(
              (product) => product.id === line.product_id,
            );
            return (
              <div className="quote-line" key={line.product_id}>
                <div className="line-heading">
                  <span className="product-thumb">
                    <span />
                  </span>
                  <div>
                    <strong>{p?.sku ?? "Product unavailable"}</strong>
                    <span>{p?.name}</span>
                  </div>
                  <button
                    className="icon-button"
                    aria-label={`Remove ${p?.sku ?? "product"}`}
                    onClick={() => {
                      setLines(lines.filter((_, i) => i !== index));
                      setDirty(true);
                    }}
                  >
                    <Trash2 />
                  </button>
                </div>
                <div className="line-commercial">
                  <label>
                    Quantity
                    <Input
                      aria-label={`Quantity for ${p?.sku}`}
                      type="number"
                      min={p?.pack_size ?? 1}
                      step={p?.pack_size ?? 1}
                      max={10000}
                      value={line.quantity}
                      onChange={(event) => {
                        setLines(
                          lines.map((value, i) =>
                            i === index
                              ? {
                                  ...value,
                                  quantity: Number(event.target.value),
                                }
                              : value,
                          ),
                        );
                        setDirty(true);
                      }}
                    />
                  </label>
                  <div>
                    <span>Unit price</span>
                    <strong>{p ? money(p.price) : "—"}</strong>
                  </div>
                  <span className="stock-label">
                    {p?.available ?? 0} available
                  </span>
                </div>
                <div className="line-evidence">
                  <BookOpenCheck />
                  <span>Catalog evidence · Page {p?.page ?? 1}</span>
                  {p && (
                    <DocumentButton
                      path={`/sources/${p.source_id}/pdf`}
                      title={`${p.sku} · Original catalog`}
                      label="View"
                      page={p.page}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
        <div className="add-product">
          <label className="sr-only" htmlFor="product-selection">
            Choose catalog product
          </label>
          <select
            id="product-selection"
            value={selected}
            onChange={(event) => setSelected(event.target.value)}
          >
            <option value="">Choose a product…</option>
            {available.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} · {p.name}
              </option>
            ))}
          </select>
          <Button
            variant="outline"
            size="icon"
            aria-label="Add selected product"
            onClick={addProduct}
            disabled={!selected}
          >
            <Plus />
          </Button>
        </div>
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
                  setDiscount(event.target.value);
                  setDirty(true);
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
                  setShipping(event.target.value);
                  setDirty(true);
                }}
              />
            </label>
          </div>
          <small>Discounts require administrator access.</small>
        </details>
        {quote && !dirty && (
          <div className="quote-totals">
            <div>
              <span>Subtotal</span>
              <strong>{money(quote.content.subtotal)}</strong>
            </div>
            <div>
              <span>Discount</span>
              <span>−{money(quote.content.discount)}</span>
            </div>
            <div>
              <span>Shipping</span>
              <span>{money(quote.content.shipping)}</span>
            </div>
            <div className="quote-grand-total">
              <span>
                Total <small>USD</small>
              </span>
              <strong>{money(quote.content.total)}</strong>
            </div>
            <p>Tax excluded. Valid for 7 days. Stock is not reserved.</p>
          </div>
        )}
        {dirty && (
          <div className="unsaved-note">
            Save a new revision to calculate the total. Any previous approval
            will be invalidated.
          </div>
        )}
        {quote && (
          <div className="quote-terms">
            <ShieldCheck />
            <p>
              {quote.content.terms}
              <br />
              Availability is observed, not reserved.
            </p>
          </div>
        )}
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
      <footer className="quotation-actions">
        {!quote ||
        dirty ||
        quote.status === "rejected" ||
        quote.status === "superseded" ? (
          <Button
            size="lg"
            disabled={!lines.length || action.isPending}
            onClick={saveDraft}
          >
            {action.isPending ? "Saving revision…" : "Save quotation revision"}
            <Check data-icon="inline-end" />
          </Button>
        ) : quote.status === "review" ? (
          <>
            <div className="approval-summary">
              Approving revision {quote.revision} for{" "}
              {capture ? "this customer" : conversation.customer_name}.<br />
              It will queue delivery through{" "}
              {conversation.channel === "local_test"
                ? "the local test channel"
                : "WhatsApp"}
              .
            </div>
            <Button
              size="lg"
              disabled={action.isPending || conversation.owner === "staff"}
              onClick={() => decide("approve")}
            >
              <ShieldCheck data-icon="inline-start" />
              {action.isPending
                ? "Recording decision…"
                : "Approve & queue delivery"}
            </Button>
            <Button
              variant="ghost"
              disabled={action.isPending}
              onClick={() => decide("reject")}
            >
              Request changes
            </Button>
          </>
        ) : (
          <Status value={quote.status} />
        )}
        {quote && !capture && (
          <DocumentButton
            path={`/quotes/${quote.id}/pdf`}
            title={`${quote.number} · Revision ${quote.revision}`}
          />
        )}
        <span className="review-footnote">
          Your approval is tied to this exact revision.
        </span>
      </footer>
    </aside>
  );
}
