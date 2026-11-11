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
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import { useCancelOrder, type OrderRow } from "./api";

/**
 * Form that cancels one customer order with a reason of 3 to 200 characters. Inputs: the `order`
 * and `onDone`. Side effects: one idempotent POST; on success stock is released (pending) or
 * returned (confirmed) by the server, the inventory, workspace and conversation queries refresh
 * and the dialog closes. The customer is not messaged; the conversation moves to "Needs your
 * attention". Errors: the server's plain sentence (for example 409 already cancelled) is inline.
 */
function CancelForm({ order, onDone }: { order: OrderRow; onDone: () => void }) {
  const id = useId();
  const [reason, setReason] = useState("");
  const cancel = useCancelOrder();
  const valid = reason.trim().length >= 3 && reason.trim().length <= 200;
  /** Send the cancellation once the reason is valid. */
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!valid) return;
    cancel.mutate(
      { orderId: order.id, reason: reason.trim() },
      { onSuccess: onDone },
    );
  }
  return (
    <form onSubmit={submit} className="inv-form">
      <DialogHeader>
        <DialogTitle>Cancel order {order.number}</DialogTitle>
        <DialogDescription>
          {order.status === "pending"
            ? "The stock held for this order is released."
            : "The confirmed quantities return to on-hand stock."}{" "}
          The customer is not messaged automatically.
        </DialogDescription>
      </DialogHeader>
      <div className="inv-field">
        <Label htmlFor={id}>Reason (3 to 200 characters)</Label>
        <Textarea
          id={id}
          value={reason}
          maxLength={200}
          onChange={(event) => setReason(event.target.value)}
          placeholder="For example: customer asked to cancel by phone"
        />
      </div>
      {cancel.isError && (
        <p className="error-text" role="alert">
          {cancel.error.message}
        </p>
      )}
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onDone}>
          Keep order
        </Button>
        <Button
          type="submit"
          variant="destructive"
          disabled={!valid || cancel.isPending}
        >
          {cancel.isPending ? "Cancelling…" : "Cancel order"}
        </Button>
      </DialogFooter>
    </form>
  );
}

/** Modal wrapper that mounts a fresh `CancelForm` per order; closes through `onClose`. */
export function CancelOrderDialog({
  order,
  onClose,
}: {
  order: OrderRow | null;
  onClose: () => void;
}) {
  return (
    <Dialog open={order !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        {order && <CancelForm key={order.id} order={order} onDone={onClose} />}
      </DialogContent>
    </Dialog>
  );
}
