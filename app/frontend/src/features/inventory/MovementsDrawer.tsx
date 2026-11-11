import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Skeleton } from "@/shared/ui/skeleton";
import { useMovements, type StockRow } from "./api";

const KIND_LABELS: Record<string, string> = {
  opening: "Opening balance",
  adjustment: "Manual adjustment",
  receipt: "Supplier receipt",
  order: "Customer order",
  order_cancel: "Order cancelled",
};

/**
 * Newest-first movement history of one product in a right-hand drawer. Inputs: the product `row`
 * (null closes it) and `onClose`. Data: `GET /inventory/movements` paged 50 at a time with a
 * "Load older movements" button. Each row names its source document (`reference`: the purchase order number for a receipt, the order number for an order movement) when the API has one. The sign of each change is written (+ or -), not only coloured.
 */
function MovementList({ row }: { row: StockRow }) {
  const movements = useMovements(row.product_id);
  const items = movements.data?.pages.flatMap((page) => page.items) ?? [];
  return (
    <div className="inv-drawer-body">
      {movements.isPending && <Skeleton className="h-24 w-full" />}
      {movements.isError && (
        <p className="error-text" role="alert">
          {movements.error.message}
        </p>
      )}
      {movements.data && items.length === 0 && (
        <p className="empty-copy">No movements recorded for this product.</p>
      )}
      <ol className="inv-movements" aria-label={`Movements for ${row.sku}`}>
        {items.map((item) => (
          <li key={item.id}>
            <strong className="inv-delta">
              {item.delta > 0 ? `+${item.delta}` : `${item.delta}`}
            </strong>
            <div>
              <span>
                {KIND_LABELS[item.kind] ?? item.kind}
                {item.reference ? ` · ${item.reference}` : ""}
              </span>
              {item.reason && <small>{item.reason}</small>}
              <time dateTime={item.created_at}>
                {new Date(item.created_at).toLocaleString("en-US", {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </time>
            </div>
          </li>
        ))}
      </ol>
      {movements.hasNextPage && (
        <Button
          variant="outline"
          disabled={movements.isFetchingNextPage}
          onClick={() => movements.fetchNextPage()}
        >
          {movements.isFetchingNextPage
            ? "Loading…"
            : "Load older movements"}
        </Button>
      )}
    </div>
  );
}

/** Drawer wrapper: open while a product is chosen; Escape or the close button calls `onClose`. */
export function MovementsDrawer({
  row,
  onClose,
}: {
  row: StockRow | null;
  onClose: () => void;
}) {
  return (
    <Dialog open={row !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent side="right">
        <DialogHeader>
          <DialogTitle>Movement history{row ? ` · ${row.sku}` : ""}</DialogTitle>
          <DialogDescription>
            {row?.name}. On hand {row?.on_hand}, reserved {row?.reserved}.
          </DialogDescription>
        </DialogHeader>
        {row && <MovementList key={row.product_id} row={row} />}
      </DialogContent>
    </Dialog>
  );
}
