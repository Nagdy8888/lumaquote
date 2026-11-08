import { Link } from "react-router-dom";
import { ArrowUpRight, BellRing } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Skeleton } from "@/shared/ui/skeleton";
import { useAcknowledgeAlert, useAlerts, type AlertRow } from "./api";
import { StockChip, stockState } from "./StatusChip";

/** Plain sentence for one stored alert, using only the fields the API sent. */
function describe(alert: AlertRow): string {
  const product = alert.sku ? `${alert.sku}${alert.name ? ` · ${alert.name}` : ""}` : "a product";
  if (alert.kind === "shortage")
    return `Shortage: a customer asked for ${alert.requested ?? "more"} of ${product}, only ${alert.available ?? 0} available. The customer was not told.`;
  return `A customer tried to accept a quotation that could no longer be accepted${alert.sku ? ` (${product})` : ""}.`;
}

/** One stored alert with an Acknowledge button (any staff role); errors are shown inline. */
function AlertItem({ alert }: { alert: AlertRow }) {
  const ack = useAcknowledgeAlert();
  return (
    <li className="inv-card" data-kind={alert.kind}>
      <header>
        <div>
          <h3>{alert.kind === "shortage" ? "Shortage" : "Acceptance refused"}</h3>
          <small>{new Date(alert.created_at).toLocaleString("en-US")}</small>
        </div>
      </header>
      <p>{describe(alert)}</p>
      <footer>
        {alert.conversation_id && (
          <Link to={`/inbox/${alert.conversation_id}`} className="inv-link">
            Open conversation
            <ArrowUpRight />
          </Link>
        )}
        <Button
          size="sm"
          variant="outline"
          disabled={ack.isPending}
          onClick={() => ack.mutate({ alertId: alert.id })}
        >
          {ack.isPending ? "Acknowledging…" : "Acknowledge"}
        </Button>
        {ack.isError && (
          <p className="error-text" role="alert">
            {ack.error.message}
          </p>
        )}
      </footer>
    </li>
  );
}

/**
 * Open alerts: stored shortage and refused-acceptance alerts (acknowledge any staff role) and the
 * live low-stock list (never stored, clears itself when stock is restored). Data:
 * `GET /inventory/alerts`, shared with the navigation badge.
 */
export function AlertsTab() {
  const alerts = useAlerts();
  if (alerts.isPending) return <Skeleton className="h-40 w-full" />;
  if (alerts.isError)
    return (
      <p className="error-text" role="alert">
        {alerts.error.message}
      </p>
    );
  const { alerts: stored, low_stock: low } = alerts.data;
  if (stored.length === 0 && low.length === 0)
    return (
      <div className="inv-empty">
        <BellRing />
        <h2>Nothing needs attention.</h2>
        <p>Shortages, refused acceptances and low stock appear here.</p>
      </div>
    );
  return (
    <div className="inv-panel">
      {stored.length > 0 && (
        <ul className="inv-cards" aria-label="Open alerts">
          {stored.map((alert) => (
            <AlertItem key={alert.id} alert={alert} />
          ))}
        </ul>
      )}
      {low.length > 0 && (
        <section aria-labelledby="inv-low-title">
          <h2 id="inv-low-title" className="inv-subtitle">
            Low stock ({low.length})
          </h2>
          <div className="inv-scroll">
            <table className="inv-table">
              <caption className="sr-only">Products at or below their reorder level</caption>
              <thead>
                <tr>
                  <th scope="col">SKU</th>
                  <th scope="col">Name</th>
                  <th scope="col" className="num">Available</th>
                  <th scope="col" className="num">Reorder level</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {low.map((row) => (
                  <tr key={row.product_id}>
                    <th scope="row" className="inv-sku">{row.sku}</th>
                    <td>{row.name}</td>
                    <td className="num"><strong>{row.available}</strong></td>
                    <td className="num">{row.reorder_level}</td>
                    <td><StockChip state={stockState(row)} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
