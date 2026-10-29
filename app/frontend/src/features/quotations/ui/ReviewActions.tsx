import type { ConversationDetail } from "@/shared/api/types";
import { Check, ShieldCheck } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Status } from "@/shared/ui/status";
import { DocumentButton } from "@/shared/ui/document-button";
/** Present exact-revision review actions and truthful delivery destination, requiring server-confirmed mutation outcomes. */
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
            disabled={pending || conversation.owner === "staff"}
            onClick={() => onDecide("approve")}
          >
            <ShieldCheck data-icon="inline-start" />
            {pending ? "Recording decision…" : "Approve & queue delivery"}
          </Button>
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
