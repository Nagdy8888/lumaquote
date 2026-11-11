/** Conversation statuses where the quotation workflow is finished or has moved to an order. */
const NOT_OPEN = ["quoted", "order_pending", "declined", "ordered"];

/**
 * Whether a conversation still counts as an open customer request on the overview. Input: the
 * server's conversation status. Output: false for `quoted` (offer sent), `order_pending` (the
 * customer accepted; staff confirm it on the stock card), `declined` (the customer said no) and
 * `ordered` (order confirmed); true for everything else, including `needs_staff`. Pure.
 */
export function isOpenConversation(status: string): boolean {
  return !NOT_OPEN.includes(status);
}
