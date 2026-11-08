import { PackageCheck } from "lucide-react";
import { useOrders } from "./api";
import { OrderActions } from "./OrderActions";

/**
 * Banner for the quotation panel: "Customer accepted LQ-… revision n" with Confirm order and
 * Cancel order, shown only while this conversation has a pending order. Inputs: the
 * `conversationId` and the displayed `quoteNumber` (null when there is no quote yet). Data: the
 * API has no per-conversation filter, so the pending-orders list (`GET /orders?status=pending`,
 * shared with the overview card) is narrowed here by `conversation_id`. Renders nothing while
 * loading, on error or when no pending order exists, so an unrelated failure never hides the
 * quotation workspace. Authority: any staff role may act; the server checks state and role.
 */
export function OrderBanner({
  conversationId,
  quoteNumber,
}: {
  conversationId: string;
  quoteNumber: string | null;
}) {
  const orders = useOrders("pending");
  const order = orders.data?.items.find(
    (item) => item.conversation_id === conversationId,
  );
  if (!order) return null;
  return (
    <section className="order-banner" aria-label="Customer order awaiting confirmation">
      <div className="order-banner-text">
        <PackageCheck aria-hidden="true" />
        <div>
          <strong>
            Customer accepted {quoteNumber ?? order.number} revision{" "}
            {order.revision}
          </strong>
          <small>
            Order {order.number}. Confirming moves the held stock out of
            on-hand. Cancelling releases it.
          </small>
        </div>
      </div>
      <OrderActions order={order} />
    </section>
  );
}
