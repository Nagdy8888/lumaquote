import { useId, useState, type FormEvent } from "react";
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
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import { useAdjust, type StockRow } from "./api";

/**
 * Admin form that corrects one product's on-hand stock by a signed whole number with a reason of
 * 3 to 200 characters. Inputs: the product `row` (its current position is shown) and `onDone`.
 * Side effects: one idempotent POST on submit; on success the inventory queries refresh and the
 * dialog closes. Errors: the server's plain sentence (403 admin only, 409 stock would drop below
 * the quantity reserved) is shown inline and the typed values stay. Nothing is optimistic.
 */
function AdjustForm({ row, onDone }: { row: StockRow; onDone: () => void }) {
  const ids = { delta: useId(), reason: useId() };
  const [delta, setDelta] = useState("");
  const [reason, setReason] = useState("");
  const adjust = useAdjust();
  const amount = Number(delta);
  const validAmount = delta.trim() !== "" && Number.isInteger(amount) && amount !== 0;
  const validReason = reason.trim().length >= 3 && reason.trim().length <= 200;
  /** Send the adjustment once the fields are valid. */
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!validAmount || !validReason) return;
    adjust.mutate(
      { product_id: row.product_id, delta: amount, reason: reason.trim() },
      { onSuccess: onDone },
    );
  }
  return (
    <form onSubmit={submit} className="inv-form">
      <DialogHeader>
        <DialogTitle>Adjust stock · {row.sku}</DialogTitle>
        <DialogDescription>
          {row.name}. On hand {row.on_hand}, reserved {row.reserved}, available{" "}
          {row.available}. On hand cannot drop below the reserved quantity.
        </DialogDescription>
      </DialogHeader>
      <div className="inv-field">
        <Label htmlFor={ids.delta}>Change in quantity (use a minus sign to remove)</Label>
        <Input
          id={ids.delta}
          type="number"
          step={1}
          inputMode="numeric"
          value={delta}
          onChange={(event) => setDelta(event.target.value)}
          placeholder="For example 25 or -3"
          aria-invalid={delta !== "" && !validAmount}
        />
        {delta !== "" && !validAmount && (
          <small className="inv-hint">Enter a whole number other than zero.</small>
        )}
        {validAmount && (
          <small className="inv-hint">
            On hand will become {row.on_hand + amount}.
          </small>
        )}
      </div>
      <div className="inv-field">
        <Label htmlFor={ids.reason}>Reason (3 to 200 characters)</Label>
        <Textarea
          id={ids.reason}
          value={reason}
          maxLength={200}
          onChange={(event) => setReason(event.target.value)}
          placeholder="For example: stock count, damaged in transit"
        />
      </div>
      {adjust.isError && (
        <p className="error-text" role="alert">
          {adjust.error.message}
        </p>
      )}
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={!validAmount || !validReason || adjust.isPending}
        >
          {adjust.isPending ? "Applying…" : "Apply adjustment"}
        </Button>
      </DialogFooter>
    </form>
  );
}

/** Modal wrapper that mounts a fresh `AdjustForm` per product; closes through `onClose`. */
export function AdjustDialog({
  row,
  onClose,
}: {
  row: StockRow | null;
  onClose: () => void;
}) {
  return (
    <Dialog open={row !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        {row && <AdjustForm key={row.product_id} row={row} onDone={onClose} />}
      </DialogContent>
    </Dialog>
  );
}
