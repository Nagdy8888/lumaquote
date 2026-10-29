import { useEffect, useState } from "react";
import type { ConversationDetail } from "@/shared/api/types";

export type EditableLine = { product_id: string; quantity: number };

/** Preserve unsaved commercial edits across remote updates and bind saving to the version observed when editing began. */
export function useQuotationDraft(detail: ConversationDetail) {
  const { quote, conversation } = detail;
  const [lines, setLines] = useState<EditableLine[]>(
    quote?.content.lines.map((line) => ({
      product_id: line.product_id,
      quantity: line.quantity,
    })) ?? [],
  );
  const [discount, setDiscount] = useState(
    quote?.content.discount_percent ?? "0",
  );
  const [shipping, setShipping] = useState(quote?.content.shipping ?? "0");
  const [dirty, setDirty] = useState(false);
  const [baseVersion, setBaseVersion] = useState(conversation.version);
  const [baseQuote, setBaseQuote] = useState(quote?.id);
  /** Load a newly persisted canonical revision only when it cannot overwrite staff's local unsaved changes. */
  useEffect(
    /** Synchronize immutable revision fields after a confirmed save or explicit local reset. */
    function reconcileCanonicalRevision() {
      if (dirty) return;
      setLines(
        quote?.content.lines.map((line) => ({
          product_id: line.product_id,
          quantity: line.quantity,
        })) ?? [],
      );
      setDiscount(quote?.content.discount_percent ?? "0");
      setShipping(quote?.content.shipping ?? "0");
      setBaseVersion(conversation.version);
      setBaseQuote(quote?.id);
    },
    [quote?.id, dirty],
  );

  /** Capture the current authoritative precondition once, before the first edit in this local draft. */
  function beginEdit() {
    if (!dirty) {
      setBaseVersion(conversation.version);
      setBaseQuote(quote?.id);
    }
    setDirty(true);
  }
  /** Replace product selections without allowing background queries to advance their mutation precondition. */
  function updateLines(value: EditableLine[]) {
    beginEdit();
    setLines(value);
  }
  /** Record an unsaved discount string; the backend validates authority, range, and monetary precision. */
  function updateDiscount(value: string) {
    beginEdit();
    setDiscount(value);
  }
  /** Record an unsaved shipping value without performing business arithmetic in the browser. */
  function updateShipping(value: string) {
    beginEdit();
    setShipping(value);
  }
  /** Finish editing only after the mutation and canonical cache reconciliation have completed. */
  function markSaved() {
    setDirty(false);
  }
  /** Explicitly discard only local unsaved fields and reload the latest server-confirmed revision. */
  function discardEdits() {
    setDirty(false);
    setLines(
      quote?.content.lines.map((line) => ({
        product_id: line.product_id,
        quantity: line.quantity,
      })) ?? [],
    );
    setDiscount(quote?.content.discount_percent ?? "0");
    setShipping(quote?.content.shipping ?? "0");
    setBaseVersion(conversation.version);
    setBaseQuote(quote?.id);
  }
  return {
    lines,
    discount,
    shipping,
    dirty,
    baseVersion,
    conflict:
      dirty &&
      (baseVersion !== conversation.version || baseQuote !== quote?.id),
    updateLines,
    updateDiscount,
    updateShipping,
    markSaved,
    discardEdits,
  };
}
