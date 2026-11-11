import "./inventory.css";
import { Link } from "react-router-dom";
import { ArrowUpRight, Boxes } from "lucide-react";
import { useAlerts, useOrders } from "./api";

/**
 * Overview card for stock, linking to `/inventory`. Data: the alerts counts and the pending-orders
 * list, both shared with the navigation badge and the order banner, so no extra request is made.
 * "Low / out of stock" is the live low-stock list (`counts.low_stock`); "Open alerts" is
 * `counts.total` (stored shortage and refused-acceptance alerts plus low-stock products), the very
 * number on the Inventory navigation badge and the Alerts tab, so the three places never disagree.
 * While a query is loading or failed the number shows an em dash rather than a made-up zero. The
 * two-digit zero padding is the overview's own style (every metric in `Overview` uses it).
 */
export function StockCard() {
  const alerts = useAlerts();
  const pending = useOrders("pending");
  const low = alerts.data?.counts.low_stock;
  const open = alerts.data?.counts.total;
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
          <dt>Low / out of stock</dt>
          <dd>{show(low)}</dd>
        </div>
        <div>
          <dt>Orders to confirm</dt>
          <dd>{show(orders)}</dd>
        </div>
        <div title="Low-stock products plus shortage and refused-acceptance alerts; the same number as the Inventory badge.">
          <dt>Open alerts</dt>
          <dd>{show(open)}</dd>
        </div>
      </dl>
    </Link>
  );
}
