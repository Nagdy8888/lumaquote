import { useState } from "react";
import { PackagePlus, Truck } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Skeleton } from "@/shared/ui/skeleton";
import { money } from "@/shared/ui/status";
import {
  useCancelPurchaseOrder,
  usePurchaseOrders,
  type PurchaseOrderRow,
} from "./api";
import { NewPurchaseOrderDialog } from "./NewPurchaseOrderDialog";
import { ReceiveDialog } from "./ReceiveDialog";
import { PurchaseChip } from "./StatusChip";

/**
 * Cancel control for one purchase order. Only an order that has received nothing can be cancelled
 * (the server refuses otherwise), so the button is absent once any quantity arrived. One
 * idempotent POST; errors are shown inline.
 */
function CancelPurchase({ order }: { order: PurchaseOrderRow }) {
  const cancel = useCancelPurchaseOrder();
  return (
    <>
      <Button
        size="sm"
        variant="outline"
        disabled={cancel.isPending}
        onClick={() => cancel.mutate({ orderId: order.id })}
      >
        {cancel.isPending ? "Cancelling…" : "Cancel purchase order"}
      </Button>
      {cancel.isError && (
        <p className="error-text" role="alert">
          {cancel.error.message}
        </p>
      )}
    </>
  );
}

/**
 * Supplier purchase orders. Input: `isAdmin`. Everyone sees the orders and their lines; only
 * administrators see "New purchase order", Receive goods and Cancel (hiding is a convenience, the
 * server returns 403 to a salesperson). Status chips carry text, not colour alone.
 */
export function PurchaseOrdersTab({ isAdmin }: { isAdmin: boolean }) {
  const orders = usePurchaseOrders();
  const [creating, setCreating] = useState(false);
  const [receiving, setReceiving] = useState<PurchaseOrderRow | null>(null);
  if (orders.isPending) return <Skeleton className="h-40 w-full" />;
  if (orders.isError)
    return (
      <p className="error-text" role="alert">
        {orders.error.message}
      </p>
    );
  const items = orders.data.items;
  return (
    <div className="inv-panel">
      {isAdmin && (
        <div className="inv-filters">
          <Button onClick={() => setCreating(true)}>
            <PackagePlus data-icon="inline-start" />
            New purchase order
          </Button>
        </div>
      )}
      {items.length === 0 ? (
        <div className="inv-empty">
          <Truck />
          <h2>No purchase orders yet.</h2>
          <p>
            {isAdmin
              ? "Record goods ordered from a supplier; stock rises when you receive them."
              : "An administrator records goods ordered from suppliers here."}
          </p>
        </div>
      ) : (
        <ul className="inv-cards" aria-label="Purchase orders">
          {items.map((order) => {
            const received = order.lines.some((l) => l.quantity_received > 0);
            const outstanding = order.lines.some(
              (l) => l.quantity_ordered > l.quantity_received,
            );
            return (
              <li key={order.id} className="inv-card" data-status={order.status}>
                <header>
                  <div>
                    <h3>{order.number}</h3>
                    <small>
                      {order.supplier}
                      {order.expected_on && ` · expected ${order.expected_on}`}
                    </small>
                  </div>
                  <PurchaseChip status={order.status} />
                </header>
                <ul className="inv-lines">
                  {order.lines.map((line) => (
                    <li key={line.product_id}>
                      <span>
                        {line.sku} · {line.name}
                      </span>
                      <span>
                        {line.quantity_received} of {line.quantity_ordered}{" "}
                        received · {money(line.unit_cost)} each
                      </span>
                    </li>
                  ))}
                </ul>
                {order.notes && <p className="inv-note">{order.notes}</p>}
                {isAdmin &&
                  (order.status === "ordered" ||
                    order.status === "partially_received") && (
                    <footer>
                      {outstanding && (
                        <Button size="sm" onClick={() => setReceiving(order)}>
                          Receive goods
                        </Button>
                      )}
                      {!received && <CancelPurchase order={order} />}
                    </footer>
                  )}
              </li>
            );
          })}
        </ul>
      )}
      <NewPurchaseOrderDialog open={creating} onClose={() => setCreating(false)} />
      <ReceiveDialog order={receiving} onClose={() => setReceiving(null)} />
    </div>
  );
}
