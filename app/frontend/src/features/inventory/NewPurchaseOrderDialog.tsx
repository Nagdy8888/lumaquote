import { useId, useState, type FormEvent } from "react";
import { Plus, Trash2 } from "lucide-react";
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
import {
  useCreatePurchaseOrder,
  useStock,
  type PurchaseOrderInput,
} from "./api";

const MAX_LINES = 100;

type DraftLine = { id: number; product: string; quantity: string; cost: string };

/**
 * Check one draft line against the API bounds: a chosen product, a whole quantity 1 to 100000 and a
 * unit cost from 0 to 1,000,000 with at most two decimals. Pure; true when the line may be sent.
 */
export function lineIsValid(line: DraftLine): boolean {
  const quantity = Number(line.quantity);
  return (
    line.product !== "" &&
    line.quantity.trim() !== "" &&
    Number.isInteger(quantity) &&
    quantity >= 1 &&
    quantity <= 100000 &&
    /^\d{1,7}(\.\d{1,2})?$/.test(line.cost.trim()) &&
    Number(line.cost) <= 1000000
  );
}

/**
 * Admin form that records a supplier purchase order: supplier (1 to 120 characters), optional
 * expected date and notes (up to 500), and 1 to 100 lines, each a distinct product with a quantity
 * and unit cost (informational; cost does not value stock). The product picker lists only
 * products not already on another line, and says so when discontinued products are left out (the API refuses them too). Side effects: one idempotent POST; on success the
 * inventory queries refresh and the dialog closes. Errors: the server's sentence is shown inline.
 */
function NewOrderForm({ onDone }: { onDone: () => void }) {
  const ids = { supplier: useId(), expected: useId(), notes: useId() };
  const stock = useStock();
  const create = useCreatePurchaseOrder();
  const [supplier, setSupplier] = useState("");
  const [expected, setExpected] = useState("");
  const [notes, setNotes] = useState("");
  const [next, setNext] = useState(2);
  const [lines, setLines] = useState<DraftLine[]>([
    { id: 1, product: "", quantity: "", cost: "" },
  ]);
  const all = stock.data?.items ?? [];
  const products = all.filter((p) => !p.discontinued);
  const hidden = all.length - products.length;
  const valid =
    supplier.trim().length >= 1 &&
    supplier.trim().length <= 120 &&
    lines.length >= 1 &&
    lines.every(lineIsValid);
  /** Patch one draft line by id. */
  function patch(id: number, change: Partial<DraftLine>) {
    setLines((current) =>
      current.map((line) => (line.id === id ? { ...line, ...change } : line)),
    );
  }
  /** Append an empty line while the 100-line limit allows it. */
  function addLine() {
    setLines((current) => [
      ...current,
      { id: next, product: "", quantity: "", cost: "" },
    ]);
    setNext(next + 1);
  }
  /** Send the purchase order once every field is valid. */
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!valid) return;
    const body: PurchaseOrderInput = {
      supplier: supplier.trim(),
      expected_on: expected || null,
      notes: notes.trim() || null,
      lines: lines.map((line) => ({
        product_id: line.product,
        quantity: Number(line.quantity),
        unit_cost: Number(line.cost).toFixed(2),
      })),
    };
    create.mutate(body, { onSuccess: onDone });
  }
  return (
    <form onSubmit={submit} className="inv-form">
      <DialogHeader>
        <DialogTitle>New purchase order</DialogTitle>
        <DialogDescription>
          Record goods ordered from a supplier. Stock rises only when you
          receive the goods.
        </DialogDescription>
      </DialogHeader>
      <div className="inv-field">
        <Label htmlFor={ids.supplier}>Supplier</Label>
        <Input
          id={ids.supplier}
          value={supplier}
          maxLength={120}
          onChange={(event) => setSupplier(event.target.value)}
        />
      </div>
      <div className="inv-field">
        <Label htmlFor={ids.expected}>Expected delivery date (optional)</Label>
        <Input
          id={ids.expected}
          type="date"
          value={expected}
          onChange={(event) => setExpected(event.target.value)}
        />
      </div>
      <fieldset className="inv-lines-editor">
        <legend>Lines ({lines.length} of {MAX_LINES})</legend>
        {hidden > 0 && (
          <p className="inv-hint">Discontinued products are not listed.</p>
        )}
        {lines.map((line, index) => {
          const taken = new Set(
            lines.filter((other) => other.id !== line.id).map((o) => o.product),
          );
          return (
            <div className="inv-line-row" key={line.id}>
              <select
                aria-label={`Product for line ${index + 1}`}
                value={line.product}
                onChange={(event) => patch(line.id, { product: event.target.value })}
              >
                <option value="">Choose a product…</option>
                {products
                  .filter((p) => !taken.has(p.product_id))
                  .map((p) => (
                    <option key={p.product_id} value={p.product_id}>
                      {p.sku} · {p.name}
                    </option>
                  ))}
              </select>
              <Input
                aria-label={`Quantity for line ${index + 1}`}
                type="number"
                min={1}
                max={100000}
                step={1}
                placeholder="Qty"
                value={line.quantity}
                onChange={(event) => patch(line.id, { quantity: event.target.value })}
              />
              <Input
                aria-label={`Unit cost in USD for line ${index + 1}`}
                type="number"
                min={0}
                max={1000000}
                step="0.01"
                placeholder="Unit cost"
                value={line.cost}
                onChange={(event) => patch(line.id, { cost: event.target.value })}
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={`Remove line ${index + 1}`}
                disabled={lines.length === 1}
                onClick={() =>
                  setLines((current) => current.filter((l) => l.id !== line.id))
                }
              >
                <Trash2 />
              </Button>
            </div>
          );
        })}
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={lines.length >= MAX_LINES || lines.length >= products.length}
          onClick={addLine}
        >
          <Plus data-icon="inline-start" />
          Add line
        </Button>
      </fieldset>
      <div className="inv-field">
        <Label htmlFor={ids.notes}>Notes (optional, up to 500 characters)</Label>
        <Textarea
          id={ids.notes}
          value={notes}
          maxLength={500}
          onChange={(event) => setNotes(event.target.value)}
        />
      </div>
      {create.isError && (
        <p className="error-text" role="alert">
          {create.error.message}
        </p>
      )}
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={!valid || create.isPending}>
          {create.isPending ? "Saving…" : "Create purchase order"}
        </Button>
      </DialogFooter>
    </form>
  );
}

/** Modal wrapper for the new purchase order form; `open` and `onClose` are controlled by the tab. */
export function NewPurchaseOrderDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="inv-wide-dialog">
        {open && <NewOrderForm onDone={onClose} />}
      </DialogContent>
    </Dialog>
  );
}
