import { Badge } from "./badge";

const labels: Record<string, string> = {
  review: "Needs approval",
  clarifying: "Awaiting reply",
  new: "New request",
  quoted: "Quotation ready",
  needs_staff: "Needs your attention",
  local_delivered: "Delivered in local test",
  approved: "Approved",
  delivery_queued: "Delivery queued",
  superseded: "Previous revision",
  configured_unverified: "Configured · unverified",
  not_connected: "Not connected",
  disabled: "Disabled",
  enabled: "Enabled",
  queued: "Queued",
  running: "Running",
  done: "Done",
  unknown: "Outcome unknown",
  failed: "Failed",
  blocked: "Blocked",
  submitted: "Submitted",
  delivered: "Delivered",
  rejected: "Rejected",
  accepted: "Customer accepted",
  declined: "Customer declined",
  order_pending: "Order to confirm",
  ordered: "Order confirmed",
};

/** Render an explicit textual status; a provider submission is never relabeled as customer delivery. */
export function Status({ value }: { value: string }) {
  return (
    <Badge variant="outline" className={`status status-${value}`}>
      {labels[value] ?? value.replaceAll("_", " ")}
    </Badge>
  );
}

/** Format server-owned USD amounts without using the browser to perform commercial calculations. */
export function money(value: string | number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(value));
}
