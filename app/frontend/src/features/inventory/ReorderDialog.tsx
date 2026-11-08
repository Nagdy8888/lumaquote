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
import { useSetReorderLevel, type StockRow } from "./api";

/**
 * Admin form that sets one product's low-stock threshold (a whole number from 0 to 100000).
 * Inputs: the product `row` and `onDone`. Side effects: one idempotent POST on submit that writes
 * no stock movement; on success the inventory queries refresh and the dialog closes. Errors: the
 * server's plain sentence is shown inline (for example 403 for a salesperson).
 */
function ReorderForm({ row, onDone }: { row: StockRow; onDone: () => void }) {
  const id = useId();
  const [level, setLevel] = useState(String(row.reorder_level));
  const save = useSetReorderLevel();
  const value = Number(level);
  const valid =
    level.trim() !== "" && Number.isInteger(value) && value >= 0 && value <= 100000;
  /** Send the new threshold once it is valid. */
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!valid) return;
    save.mutate(
      { product_id: row.product_id, reorder_level: value },
      { onSuccess: onDone },
    );
  }
  return (
    <form onSubmit={submit} className="inv-form">
      <DialogHeader>
        <DialogTitle>Reorder level · {row.sku}</DialogTitle>
        <DialogDescription>
          {row.name}. A low-stock alert appears when available stock is at or
          below this number. Available now: {row.available}.
        </DialogDescription>
      </DialogHeader>
      <div className="inv-field">
        <Label htmlFor={id}>Reorder level (0 to 100000)</Label>
        <Input
          id={id}
          type="number"
          min={0}
          max={100000}
          step={1}
          inputMode="numeric"
          value={level}
          onChange={(event) => setLevel(event.target.value)}
          aria-invalid={!valid}
        />
        {!valid && (
          <small className="inv-hint">Enter a whole number from 0 to 100000.</small>
        )}
      </div>
      {save.isError && (
        <p className="error-text" role="alert">
          {save.error.message}
        </p>
      )}
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={!valid || save.isPending}>
          {save.isPending ? "Saving…" : "Save reorder level"}
        </Button>
      </DialogFooter>
    </form>
  );
}

/** Modal wrapper that mounts a fresh `ReorderForm` per product; closes through `onClose`. */
export function ReorderDialog({
  row,
  onClose,
}: {
  row: StockRow | null;
  onClose: () => void;
}) {
  return (
    <Dialog open={row !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        {row && <ReorderForm key={row.product_id} row={row} onDone={onClose} />}
      </DialogContent>
    </Dialog>
  );
}
