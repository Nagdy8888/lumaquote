import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { downloadFile, request } from "@/shared/api/client";
import type { components } from "@/shared/api/generated";
import { useSession } from "@/shared/auth/session";

type Schemas = components["schemas"];
export type StockRow = Schemas["StockRow"];
export type StockView = Schemas["StockView"];
export type AlertsView = Schemas["AlertsView"];
export type AlertRow = Schemas["AlertRow"];
export type MovementRow = Schemas["MovementRow"];
export type MovementsPage = Schemas["MovementsPage"];
export type OrderRow = Schemas["OrderRow"];
export type OrdersView = Schemas["OrdersView"];
export type PurchaseOrderRow = Schemas["PurchaseOrderRow"];
export type PurchaseOrdersView = Schemas["PurchaseOrdersView"];
export type PurchaseOrderInput = Schemas["PurchaseOrderInput"];
export type ReceiveInput = Schemas["ReceiveInput"];
export type SheetExport = Schemas["SheetExportView"];

/** How often the sheet-export status is re-read while Apps Script has not finished (queued or claimed). */
export const SHEET_POLL_MS = 5000;
/** Fallback polling for the alert counts, because worker-side alerts write no audit revision for the live stream. */
const ALERTS_POLL_MS = 15000;

/**
 * Query keys of the inventory feature. Every key starts with `inventory` and carries the staff
 * identity so a sign-out or account switch never shows another person's cache; invalidating the
 * `["inventory"]` prefix refreshes stock, orders, alerts, purchase orders, movements and the export
 * status together. Pure.
 */
export const inventoryKeys = {
  all: ["inventory"] as const,
  stock: (user?: string) => ["inventory", "stock", user] as const,
  alerts: (user?: string) => ["inventory", "alerts", user] as const,
  orders: (user?: string, status?: string) =>
    ["inventory", "orders", user, status ?? "all"] as const,
  purchaseOrders: (user?: string) =>
    ["inventory", "purchase-orders", user] as const,
  movements: (user?: string, product?: string) =>
    ["inventory", "movements", user, product] as const,
  sheetExport: (user?: string) => ["inventory", "sheet-export", user] as const,
};

/**
 * Read the stock table (any staff role). Output: rows with on hand, reserved, available, reorder
 * level and the server's low flag. Polling is left to the shared live-update invalidation.
 */
export function useStock() {
  const { session } = useSession();
  const user = session?.user.id;
  return useQuery({
    queryKey: inventoryKeys.stock(user),
    enabled: !!session,
    /** Fetch the stock table through authenticated API access. */
    queryFn: function loadStock({ signal }) {
      return request<StockView>("/inventory/stock", { signal });
    },
    retry: 1,
  });
}

/**
 * Read open alerts (shortage, refused acceptance), the live low-stock list and their counts.
 * The counts feed the navigation badge and the overview card, so the query re-reads every 15 s.
 */
export function useAlerts() {
  const { session } = useSession();
  const user = session?.user.id;
  return useQuery({
    queryKey: inventoryKeys.alerts(user),
    enabled: !!session,
    /** Fetch alerts and counts through authenticated API access. */
    queryFn: function loadAlerts({ signal }) {
      return request<AlertsView>("/inventory/alerts", { signal });
    },
    refetchInterval: ALERTS_POLL_MS,
    retry: 1,
  });
}

/**
 * Read customer orders, newest first, optionally only one status (the API has no per-conversation
 * filter, so callers narrow by `conversation_id` themselves). `status` is `pending`, `confirmed`
 * or `cancelled`; omit it for all.
 */
export function useOrders(status?: "pending" | "confirmed" | "cancelled") {
  const { session } = useSession();
  const user = session?.user.id;
  return useQuery({
    queryKey: inventoryKeys.orders(user, status),
    enabled: !!session,
    /** Fetch the orders list, filtered by status when one was asked for. */
    queryFn: function loadOrders({ signal }) {
      const query = status ? `?status=${status}` : "";
      return request<OrdersView>(`/orders${query}`, { signal });
    },
    refetchInterval: ALERTS_POLL_MS,
    retry: 1,
  });
}

/** Read supplier purchase orders with their lines (any staff role may read; only admins may change). */
export function usePurchaseOrders() {
  const { session } = useSession();
  const user = session?.user.id;
  return useQuery({
    queryKey: inventoryKeys.purchaseOrders(user),
    enabled: !!session,
    /** Fetch purchase orders through authenticated API access. */
    queryFn: function loadPurchaseOrders({ signal }) {
      return request<PurchaseOrdersView>("/purchase-orders", { signal });
    },
    retry: 1,
  });
}

/**
 * Page through the movement history of one product, newest first, 50 per page, following the
 * server's opaque `next` cursor. Disabled until a product is chosen.
 */
export function useMovements(productId: string | null) {
  const { session } = useSession();
  const user = session?.user.id;
  return useInfiniteQuery({
    queryKey: inventoryKeys.movements(user, productId ?? ""),
    enabled: !!session && !!productId,
    initialPageParam: "" as string,
    /** Fetch one page; an empty cursor means the first page. */
    queryFn: function loadMovements({ pageParam, signal }) {
      const cursor = pageParam ? `&before=${encodeURIComponent(pageParam)}` : "";
      return request<MovementsPage>(
        `/inventory/movements?product_id=${productId}&limit=50${cursor}`,
        { signal },
      );
    },
    /** The next cursor, or undefined when this was the last page. */
    getNextPageParam: function nextCursor(last) {
      return last.next ?? undefined;
    },
    retry: 1,
  });
}

/**
 * Read the latest Google Sheets export and keep re-reading every 5 s while it is queued or claimed,
 * so the toolbar can show progress until Apps Script (about one minute) finishes. Stops on
 * none, done or failed.
 */
export function useSheetExport() {
  const { session } = useSession();
  const user = session?.user.id;
  return useQuery({
    queryKey: inventoryKeys.sheetExport(user),
    enabled: !!session,
    /** Fetch the latest export's status. */
    queryFn: function loadSheetExport({ signal }) {
      return request<SheetExport>("/inventory/sheet-exports/latest", {
        signal,
      });
    },
    /** Poll only while Apps Script has work outstanding. */
    refetchInterval: function pollWhileOpen(query) {
      const status = query.state.data?.status;
      return status === "queued" || status === "claimed"
        ? SHEET_POLL_MS
        : false;
    },
    retry: 1,
  });
}

/**
 * Build a mutation hook that POSTs JSON with a fresh `Idempotency-Key` per call, then refreshes
 * every inventory query plus the workspace (catalog availability, quote and conversation
 * statuses) and open conversations. Nothing is shown optimistically: the server answers first.
 * Inputs: a function turning the variables into `[path, body]`.
 */
function useCommand<V, R>(build: (variables: V) => [string, unknown?]) {
  const client = useQueryClient();
  return useMutation({
    /** Send the command with a new operation id; the server enforces role and state rules. */
    mutationFn: function send(variables: V) {
      const [path, body] = build(variables);
      return request<R>(
        path,
        {
          method: "POST",
          ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        },
        crypto.randomUUID(),
      );
    },
    /** Invalidate every collection a stock, order or purchase change can affect. */
    onSuccess: function reconcile() {
      return Promise.all([
        client.invalidateQueries({ queryKey: inventoryKeys.all }),
        client.invalidateQueries({ queryKey: ["workspace"] }),
        client.invalidateQueries({ queryKey: ["conversation"] }),
      ]);
    },
  });
}

/** Admin: correct one product's on-hand stock by a signed amount with a reason. */
export function useAdjust() {
  return useCommand<
    { product_id: string; delta: number; reason: string },
    Schemas["LevelView"]
  >((body) => ["/inventory/adjustments", body]);
}

/** Admin: set one product's low-stock threshold. */
export function useSetReorderLevel() {
  return useCommand<
    { product_id: string; reorder_level: number },
    Schemas["LevelView"]
  >((body) => ["/inventory/reorder-levels", body]);
}

/** Any staff role: confirm a pending order so its reserved stock leaves on-hand. */
export function useConfirmOrder() {
  return useCommand<{ orderId: string }, OrderRow>(({ orderId }) => [
    `/orders/${orderId}/confirm`,
  ]);
}

/** Any staff role: cancel a pending or confirmed order with a reason (3 to 200 characters). */
export function useCancelOrder() {
  return useCommand<{ orderId: string; reason: string }, OrderRow>(
    ({ orderId, reason }) => [`/orders/${orderId}/cancel`, { reason }],
  );
}

/** Admin: record a supplier purchase order. */
export function useCreatePurchaseOrder() {
  return useCommand<PurchaseOrderInput, PurchaseOrderRow>((body) => [
    "/purchase-orders",
    body,
  ]);
}

/** Admin: receive part or all of a purchase order, raising stock. */
export function useReceivePurchaseOrder() {
  return useCommand<
    { orderId: string; body: ReceiveInput },
    PurchaseOrderRow
  >(({ orderId, body }) => [`/purchase-orders/${orderId}/receive`, body]);
}

/** Admin: cancel a purchase order that has received nothing. */
export function useCancelPurchaseOrder() {
  return useCommand<{ orderId: string }, PurchaseOrderRow>(({ orderId }) => [
    `/purchase-orders/${orderId}/cancel`,
  ]);
}

/** Any staff role: acknowledge one open alert. */
export function useAcknowledgeAlert() {
  return useCommand<{ alertId: string }, Schemas["AlertAck"]>(
    ({ alertId }) => [`/inventory/alerts/${alertId}/acknowledge`],
  );
}

/**
 * Queue a Google Sheets stock export (or learn that one is already queued or running). The reply
 * is written straight into the status cache so polling starts at once.
 */
export function useQueueSheetExport() {
  const client = useQueryClient();
  const { session } = useSession();
  return useMutation({
    /** POST with a new operation id; the server returns the queued or running export. */
    mutationFn: function queue() {
      return request<SheetExport>(
        "/inventory/sheet-exports",
        { method: "POST" },
        crypto.randomUUID(),
      );
    },
    /** Show the queued export immediately; polling takes over from there. */
    onSuccess: function remember(data) {
      client.setQueryData(inventoryKeys.sheetExport(session?.user.id), data);
    },
  });
}

/**
 * Download the Excel workbook with the staff bearer token and hand the Blob to the browser as a
 * file named by the server. Side effects: one authenticated GET and one temporary object URL,
 * revoked right after the click. Errors surface as `ApiError` (for example the 10 per minute
 * export limit).
 */
export function useDownloadWorkbook() {
  return useMutation({
    /** Fetch the workbook and trigger the browser save. */
    mutationFn: async function download() {
      const { blob, filename } = await downloadFile(
        "/inventory/export.xlsx",
        "lumaquote-stock.xlsx",
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      return filename;
    },
  });
}
