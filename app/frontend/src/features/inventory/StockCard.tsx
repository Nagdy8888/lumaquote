import "./inventory.css";
import { Link } from "react-router-dom";
import { ArrowUpRight, Boxes } from "lucide-react";
import { useAlerts, useOrders } from "./api";

/**
 * Overview card for stock: low-stock products, pending customer orders and open alerts, linking to
 * `/inventory`. Data: the alerts counts (`low_stock`, and open alerts = `shortage` + `acceptance_refused`, so low stock is not counted twice) and the pending-orders list, both
 * shared with the navigation badge and the order banner, so no extra request is made. While a
 * query is loading or failed the number shows an em dash rather than a made-up zero.
 */
export function StockCard() {
  const alerts = useAlerts();
  const pending = useOrders("pending");
  const low = alerts.data?.counts.low_stock;
  const counts = alerts.data?.counts;
  const open = counts ? counts.shortage + counts.acceptance_refused : undefined;
  const orders = pending.data?.items.length;
  /** Format a count, or an em dash while it is unknown. */
  const show = (value: number | undefined) =>
    value === undefined ? "—" : value.toString().padStart(2, "0");
  return (
    <Link
      to="/inventory"
      className="stock-card"
      aria-label="Stock: open the inventory page"
    >
      <div className="stock-card-title">
        <Boxes aria-hidden="true" />
        <h2>Stock</h2>
        <ArrowUpRight aria-hidden="true" />
      </div>
      <dl>
        <div>
          <dt>Low-stock products</dt>
          <dd>{show(low)}</dd>
        </div>
        <div>
          <dt>Orders to confirm</dt>
          <dd>{show(orders)}</dd>
        </div>
        <div>
          <dt>Open alerts</dt>
          <dd>{show(open)}</dd>
        </div>
      </dl>
    </Link>
  );
}
