import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  Clock,
  PackageCheck,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import type { StockRow } from "./api";

type Tone = "ok" | "warn" | "bad" | "neutral";

/**
 * One status chip: always an icon plus a text label, so the state never depends on colour alone.
 * Inputs: `tone` picks the colour family, `label` is the visible and accessible text, `icon` is
 * decorative (hidden from assistive technology). Pure presentation, no side effects.
 */
function Chip({
  tone,
  label,
  icon: Icon,
}: {
  tone: Tone;
  label: string;
  icon: LucideIcon;
}) {
  return (
    <span className={`inv-chip inv-chip-${tone}`}>
      <Icon aria-hidden="true" />
      {label}
    </span>
  );
}

/**
 * Classify one stock row. Output: `out` when nothing is available (available <= 0), `low` when the
 * server flagged it at or below its reorder level (discontinued products are never flagged), else
 * `ok`. The same rule the Excel export uses. Pure; the browser never recomputes available stock.
 */
export function stockState(row: StockRow): "ok" | "low" | "out" {
  if (row.available <= 0) return "out";
  return row.low ? "low" : "ok";
}

/** Chip for a stock row: OK, Low or Out, each with its own icon and text. */
export function StockChip({ state }: { state: "ok" | "low" | "out" }) {
  if (state === "out") return <Chip tone="bad" label="Out" icon={XCircle} />;
  if (state === "low")
    return <Chip tone="warn" label="Low" icon={AlertTriangle} />;
  return <Chip tone="ok" label="OK" icon={CheckCircle2} />;
}

/** Chip for a customer order status (pending, confirmed, cancelled). */
export function OrderChip({ status }: { status: string }) {
  if (status === "pending")
    return <Chip tone="warn" label="Pending" icon={Clock} />;
  if (status === "confirmed")
    return <Chip tone="ok" label="Confirmed" icon={CheckCircle2} />;
  return <Chip tone="neutral" label="Cancelled" icon={Ban} />;
}

/** Chip for a purchase order status (ordered, partially received, received, cancelled). */
export function PurchaseChip({ status }: { status: string }) {
  if (status === "ordered")
    return <Chip tone="warn" label="Ordered" icon={Clock} />;
  if (status === "partially_received")
    return <Chip tone="warn" label="Partly received" icon={PackageCheck} />;
  if (status === "received")
    return <Chip tone="ok" label="Received" icon={CheckCircle2} />;
  return <Chip tone="neutral" label="Cancelled" icon={Ban} />;
}
