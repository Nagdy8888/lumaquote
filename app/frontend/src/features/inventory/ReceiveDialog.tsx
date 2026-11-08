import { useState, type FormEvent } from "react";
import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { useReceivePurchaseOrder, type PurchaseOrderRow } from "./api";

/**
 * Validate one receipt quantity text against the units still outstanding. Pure. Output: the whole
 * number to receive (0 for empty), or an error sentence when it is not a whole number, negative
 * or larger than `remaining`.
 */
export function receiptQuantity(
  text: string,
  remaining: number,
): { quantity: number; error: string | null } {
  if (text.trim() === "") return { quantity: 0, error: null };
  const quantity = Number(text);
  if (!Number.isInteger(quantity) || quantity < 0)
    return { quantity: 0, error: "Enter a whole number." };
  if (quantity > remaining)
    return {
      quantity,
      error: `Cannot exceed the ${remaining} still outstanding.`,
    };
  return { quantity, error: null };
}

/**
 * Admin form that receives goods against a purchase order, partly or fully. Input: the `order`;
 * each line with units outstanding gets a quantity box (0 to remaining). The button stays disabled
 * while any box exceeds what is outstanding or no box has a quantity, so over-receipt is refused
 * before it is sent (the server refuses it too). Side effects: one idempotent POST with only the
 * lines that have a quantity; stock rises by those amounts after the server answers. Receipts
 * cannot be undone; a mistake is corrected with an adjustment.
 */
function ReceiveForm({
  order,
  onDone,
}: {
  order: PurchaseOrderRow;
  onDone: () => void;
}) {
  const open = order.lines.filter((l) => l.quantity_ordered > l.quantity_received);
  const [values, setValues] = useState<Record<string, string>>({});
  const receive = useReceivePurchaseOrder();
  const checks = open.map((line) => ({
    line,
    ...receiptQuantity(
      values[line.product_id] ?? "",
      line.quantity_ordered - line.quantity_received,
    ),
  }));
  const valid =
    checks.every((c) => c.error === null) && checks.some((c) => c.quantity > 0);
  /** Send only the lines that have a quantity. */
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!valid) return;
    receive.mutate(
      {
        orderId: order.id,
        body: {
          lines: checks
            .filter((c) => c.quantity > 0)
            .map((c) => ({
              product_id: c.line.product_id,
              quantity: c.quantity,
            })),
        },
      },
      { onSuccess: onDone },
    );
  }
  return (
    <form onSubmit={submit} className="inv-form">
      <DialogHeader>
        <DialogTitle>Receive goods · {order.number}</DialogTitle>
        <DialogDescription>
          {order.supplier}. Enter what arrived; leave a line empty to receive
          nothing for it. You can receive the rest later.
        </DialogDescription>
      </DialogHeader>
      {checks.map(({ line, error }) => {
        const remaining = line.quantity_ordered - line.quantity_received;
        const inputId = `receive-${line.product_id}`;
        return (
          <div className="inv-field" key={line.product_id}>
            <label htmlFor={inputId}>
              {line.sku} · {line.name}
              <small>
                {" "}
                ordered {line.quantity_ordered}, received {line.quantity_received},
                outstanding {remaining}
              </small>
            </label>
            <Input
              id={inputId}
              type="number"
              min={0}
              max={remaining}
              step={1}
              value={values[line.product_id] ?? ""}
              aria-invalid={error !== null}
              aria-describedby={error ? `${inputId}-error` : undefined}
              onChange={(event) =>
                setValues({ ...values, [line.product_id]: event.target.value })
              }
            />
            {error && (
              <small className="inv-hint inv-hint-error" id={`${inputId}-error`}>
                {error}
              </small>
            )}
          </div>
        );
      })}
      {receive.isError && (
        <p className="error-text" role="alert">
          {receive.error.message}
        </p>
      )}
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={!valid || receive.isPending}>
          {receive.isPending ? "Receiving…" : "Receive goods"}
        </Button>
      </DialogFooter>
    </form>
  );
}

/** Modal wrapper that mounts a fresh `ReceiveForm` per purchase order; closes through `onClose`. */
export function ReceiveDialog({
  order,
  onClose,
}: {
  order: PurchaseOrderRow | null;
  onClose: () => void;
}) {
  return (
    <Dialog open={order !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        {order && <ReceiveForm key={order.id} order={order} onDone={onClose} />}
      </DialogContent>
    </Dialog>
  );
}
