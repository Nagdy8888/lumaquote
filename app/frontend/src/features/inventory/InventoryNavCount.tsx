import { useAlerts } from "./api";

/**
 * Count badge for the "Inventory" navigation item: open stored alerts plus low-stock products
 * (`counts.total` from `GET /inventory/alerts`). Renders nothing when the count is zero, still
 * loading or failed, so an inventory outage never breaks the shell. The visible number has an
 * accessible name that says what it counts.
 */
export function InventoryNavCount() {
  const alerts = useAlerts();
  const total = alerts.data?.counts.total ?? 0;
  if (total <= 0) return null;
  return (
    <span className="nav-count" aria-label={`${total} open stock items`}>
      {total}
    </span>
  );
}
