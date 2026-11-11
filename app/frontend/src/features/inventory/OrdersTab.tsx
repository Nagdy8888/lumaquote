import { Link } from "react-router-dom";
import { ArrowUpRight, ClipboardList } from "lucide-react";
import { customerName } from "@/shared/api/workspace-context";
import { Skeleton } from "@/shared/ui/skeleton";
import { money } from "@/shared/ui/status";
import { useOrders, type OrderRow } from "./api";
import { OrderActions } from "./OrderActions";
import { OrderChip } from "./StatusChip";

const VIA: Record<string, string> = {
  telegram_button: "Telegram button",
  reply: "Customer reply",
  staff: "Staff",
};

/**
 * Order the list for the desk: pending orders first (they need a decision), then the rest, each
 * group newest first as the server sent them. Pure; returns a new array.
 */
export function pendingFirst(items: OrderRow[]): OrderRow[] {
  return [
    ...items.filter((order) => order.status === "pending"),
    ...items.filter((order) => order.status !== "pending"),
  ];
}

/**
 * Customer orders created when a customer accepted a quotation. Input: `capture` (masks customer
 * names like the rest of the app). Each card shows the order number, quotation revision,
 * accepted lines at the quoted prices, total, how it was accepted and the status chip; pending
 * orders offer Confirm and Cancel, confirmed ones Cancel (any staff role; the server decides).
 */
export function OrdersTab({ capture }: { capture: boolean }) {
  const orders = useOrders();
  if (orders.isPending) return <Skeleton className="h-40 w-full" />;
  if (orders.isError)
    return (
      <p className="error-text" role="alert">
        {orders.error.message}
      </p>
    );
  const items = pendingFirst(orders.data.items);
  if (items.length === 0)
    return (
      <div className="inv-empty">
        <ClipboardList />
        <h2>No customer orders yet.</h2>
        <p>An order appears here when a customer accepts a sent quotation.</p>
      </div>
    );
  return (
    <ul className="inv-cards" aria-label="Customer orders">
      {items.map((order) => (
        <li key={order.id} className="inv-card" data-status={order.status}>
          <header>
            <div>
              <h3>{order.number}</h3>
              <small>
                {capture
                  ? "Commercial customer"
                  : order.customer_company || order.customer_name}
                {" · "}
                {customerName(order.customer_name, capture)} · revision{" "}
                {order.revision}
              </small>
            </div>
            <OrderChip status={order.status} />
          </header>
          <ul className="inv-lines">
            {order.lines.map((line) => (
              <li key={line.product_id}>
                <span>
                  {line.quantity} × {line.sku} · {line.name}
                </span>
                <span>{money(line.line_total)}</span>
              </li>
            ))}
          </ul>
          <footer>
            <span>
              Total <strong>{money(order.total)}</strong> · accepted via{" "}
              {VIA[order.accepted_via] ?? order.accepted_via} on{" "}
              {new Date(order.accepted_at).toLocaleDateString("en-US")}
              {order.cancel_reason && <> · reason: {order.cancel_reason}</>}
            </span>
            <Link to={`/inbox/${order.conversation_id}`} className="inv-link">
              Open conversation
              <ArrowUpRight />
            </Link>
            <OrderActions order={order} />
          </footer>
        </li>
      ))}
    </ul>
  );
}
