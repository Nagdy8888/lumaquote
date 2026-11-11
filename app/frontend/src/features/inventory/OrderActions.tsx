import { useState } from "react";
import { Check } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { useConfirmOrder, type OrderRow } from "./api";
import { CancelOrderDialog } from "./CancelOrderDialog";

/**
 * Confirm and Cancel controls for one customer order, usable by any staff role. Input: the
 * `order`. "Confirm order" (pending only) sends one idempotent POST; the server moves the
 * reserved stock out of on-hand and the order shows "Confirmed" only after the refetch. "Cancel
 * order" (pending or confirmed) opens the reason dialog. Errors from the server (for example 409
 * hold released, already cancelled) appear inline under the buttons. Nothing is optimistic.
 */
export function OrderActions({ order }: { order: OrderRow }) {
  const confirm = useConfirmOrder();
  const [cancelling, setCancelling] = useState<OrderRow | null>(null);
  if (order.status === "cancelled") return null;
  return (
    <div className="inv-order-actions">
      {order.status === "pending" && (
        <Button
          size="sm"
          disabled={confirm.isPending}
          onClick={() => confirm.mutate({ orderId: order.id })}
        >
          <Check data-icon="inline-start" />
          {confirm.isPending ? "Confirming…" : "Confirm order"}
        </Button>
      )}
      <Button
        size="sm"
        variant="outline"
        disabled={confirm.isPending}
        onClick={() => setCancelling(order)}
      >
        Cancel order
      </Button>
      {confirm.isError && (
        <p className="error-text" role="alert">
          {confirm.error.message}
        </p>
      )}
      <CancelOrderDialog order={cancelling} onClose={() => setCancelling(null)} />
    </div>
  );
}
