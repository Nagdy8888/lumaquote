import type { Quote } from "@/shared/api/types";
import { ShieldCheck } from "lucide-react";
import { money } from "@/shared/ui/status";
/** Present only the persisted canonical totals; unsaved edits hide obsolete totals until a new revision is calculated. */
export function QuoteSummary({
  quote,
  dirty,
}: {
  quote: Quote | null;
  dirty: boolean;
}) {
  return (
    <>
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
          Save a new revision to calculate the total. Any previous approval will
          be invalidated.
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
    </>
  );
}
