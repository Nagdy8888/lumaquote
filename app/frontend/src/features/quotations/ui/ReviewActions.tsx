import { useEffect, useRef, useState } from "react";
import type { ConversationDetail } from "@/shared/api/types";
import { Check, ShieldCheck } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Status, money } from "@/shared/ui/status";
import { DocumentButton } from "@/shared/ui/document-button";

/**
 * Present exact-revision review actions and the truthful delivery destination.
 * Approval is a two-step inline control: "Review approval" opens a panel that
 * restates quote number, revision, customer ("this customer" in capture mode), the
 * server's total string (formatted only, never calculated) and the channel; only its
 * button calls `onDecide("approve")`. Focus moves to the panel heading on open and
 * back to "Review approval" on Cancel; Escape cancels. If the displayed quote id or
 * revision changes while the panel is open, or unsaved edits begin, the panel closes
 * and (for a changed quote) says so; the decision payload still carries the
 * revision the parent captured. Nothing here shows approval or delivery before the
 * server confirms it: the parent re-renders with the stored status. Disabled while a
 * decision is pending or when staff owns the conversation. No browser dialog is used.
 */
export function ReviewActions({
  detail,
  dirty,
  hasLines,
  pending,
  capture,
  onSave,
  onDecide,
}: {
  detail: ConversationDetail;
  dirty: boolean;
  hasLines: boolean;
  pending: boolean;
  capture: boolean;
  onSave: () => void;
  onDecide: (decision: "approve" | "reject") => void;
}) {
  const { quote, conversation } = detail;
  const quoteKey = quote ? `${quote.id}:${quote.revision}` : "";
  const [openFor, setOpenFor] = useState<string | null>(null);
  const [changed, setChanged] = useState(false);
  const reviewButton = useRef<HTMLButtonElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const refocusReview = useRef(false);
  const confirming =
    openFor !== null &&
    openFor === quoteKey &&
    quote?.status === "review" &&
    !dirty;
  /** Close the panel when its quote changed, left review, or the user began editing; announce a changed quote. */
  useEffect(
    /** Compare the revision the panel was opened for with the one now displayed. */
    function closeStalePanel() {
      if (openFor === null) return;
      if (dirty || quote?.status !== "review") setOpenFor(null);
      else if (openFor !== quoteKey) {
        setOpenFor(null);
        setChanged(true);
      }
    },
    [openFor, quoteKey, dirty, quote?.status],
  );
  /** Move focus into the panel when it opens, and back to "Review approval" after Cancel or Escape. */
  useEffect(
    /** Apply the focus change after the panel or button has rendered. */
    function moveFocus() {
      if (confirming) heading.current?.focus();
      else if (refocusReview.current) {
        refocusReview.current = false;
        reviewButton.current?.focus();
      }
    },
    [confirming],
  );
  /** Open the restated-approval panel for the revision currently displayed. */
  function openPanel() {
    setChanged(false);
    setOpenFor(quoteKey);
  }
  /** Close the panel without a decision and return focus to the step-1 button. */
  function cancelPanel() {
    refocusReview.current = true;
    setOpenFor(null);
  }
  const channel =
    conversation.channel === "local_test"
      ? "the local test channel"
      : conversation.channel === "telegram"
        ? "Telegram"
        : conversation.channel === "email"
          ? "email"
          : "WhatsApp";
  const customer = capture ? "this customer" : conversation.customer_name;
  return (
    <footer className="quotation-actions">
      {!quote ||
      dirty ||
      quote.status === "rejected" ||
      quote.status === "superseded" ? (
        <Button size="lg" disabled={!hasLines || pending} onClick={onSave}>
          {pending ? "Saving revision…" : "Save quotation revision"}
          <Check data-icon="inline-end" />
        </Button>
      ) : quote.status === "review" ? (
        <>
          {changed && (
            <p className="approval-changed" role="status">
              This quotation changed. Review the new revision.
            </p>
          )}
          {confirming ? (
            <section
              className="approval-confirm"
              aria-labelledby="approval-confirm-title"
              onKeyDown={(event) => {
                if (event.key === "Escape") cancelPanel();
              }}
            >
              <h3 id="approval-confirm-title" tabIndex={-1} ref={heading}>
                Confirm approval
              </h3>
              <dl>
                <div>
                  <dt>Quotation</dt>
                  <dd>{quote.number}</dd>
                </div>
                <div>
                  <dt>Revision</dt>
                  <dd>{quote.revision}</dd>
                </div>
                <div>
                  <dt>Customer</dt>
                  <dd>{customer}</dd>
                </div>
                <div>
                  <dt>Total</dt>
                  <dd>{money(quote.content.total)}</dd>
                </div>
                <div>
                  <dt>Channel</dt>
                  <dd>{channel}</dd>
                </div>
              </dl>
              <p>
                Approving queues delivery of exactly this revision. It is
                approved only when the server confirms it.
              </p>
              <Button
                size="lg"
                disabled={pending || conversation.owner === "staff"}
                onClick={() => onDecide("approve")}
              >
                <ShieldCheck data-icon="inline-start" />
                {pending
                  ? "Recording decision…"
                  : `Approve revision ${quote.revision} & queue delivery`}
              </Button>
              <Button variant="ghost" disabled={pending} onClick={cancelPanel}>
                Cancel
              </Button>
            </section>
          ) : (
            <>
              <div className="approval-summary">
                Approving revision {quote.revision} for {customer}.<br />
                It will queue delivery through {channel}.
              </div>
              <Button
                size="lg"
                ref={reviewButton}
                disabled={pending || conversation.owner === "staff"}
                onClick={openPanel}
              >
                <ShieldCheck data-icon="inline-start" />
                Review approval
              </Button>
            </>
          )}
          <Button
            variant="ghost"
            disabled={pending}
            onClick={() => onDecide("reject")}
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
  );
}
