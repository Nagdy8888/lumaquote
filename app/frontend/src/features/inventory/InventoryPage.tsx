import "./inventory.css";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Boxes } from "lucide-react";
import { useWorkspaceContext } from "@/shared/api/workspace-context";
import { Skeleton } from "@/shared/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";
import { useAlerts, useOrders, useStock, type StockRow } from "./api";
import { AdjustDialog } from "./AdjustDialog";
import { AlertsTab } from "./AlertsTab";
import { ExportToolbar } from "./ExportToolbar";
import { MovementsDrawer } from "./MovementsDrawer";
import { OrdersTab } from "./OrdersTab";
import { PurchaseOrdersTab } from "./PurchaseOrdersTab";
import { ReorderDialog } from "./ReorderDialog";
import { StockTable } from "./StockTable";

const TABS = ["stock", "orders", "purchase-orders", "alerts"] as const;
type Tab = (typeof TABS)[number];

/**
 * The Inventory page at `/inventory`: Stock, Customer orders, Purchase orders and Alerts tabs
 * plus the Excel and Google Sheets export toolbar. The active tab lives in the `?tab=` query so
 * links from the overview and alerts can open a tab directly. Role: `data.role` from the
 * workspace shows admin-only controls (Adjust, Reorder level, purchase-order create, receive and
 * cancel) to administrators only; this hides, it does not authorize, and the server returns 403
 * otherwise. Server state is owned by TanStack Query hooks in `api.ts`.
 */
export function InventoryPage() {
  const { data, capture } = useWorkspaceContext();
  const isAdmin = data.role === "admin";
  const [params, setParams] = useSearchParams();
  const requested = params.get("tab");
  const tab: Tab = (TABS as readonly string[]).includes(requested ?? "")
    ? (requested as Tab)
    : "stock";
  const stock = useStock();
  const alerts = useAlerts();
  const pending = useOrders("pending");
  const [adjusting, setAdjusting] = useState<StockRow | null>(null);
  const [reordering, setReordering] = useState<StockRow | null>(null);
  const [history, setHistory] = useState<StockRow | null>(null);
  const alertTotal = alerts.data?.counts.total;
  const pendingTotal = pending.data?.items.length;
  return (
    <section className="inventory-page">
      <div className="page-heading">
        <div>
          <h1>Stock you can stand behind.</h1>
          <p>
            On hand, reserved and available for every product, with the orders
            and purchases that move them.
          </p>
        </div>
        <Boxes />
      </div>
      <ExportToolbar />
      <Tabs
        value={tab}
        onValueChange={(next) => setParams(next === "stock" ? {} : { tab: next })}
      >
        <TabsList aria-label="Inventory sections">
          <TabsTrigger value="stock">Stock</TabsTrigger>
          <TabsTrigger value="orders">
            Customer orders{pendingTotal ? ` (${pendingTotal} pending)` : ""}
          </TabsTrigger>
          <TabsTrigger value="purchase-orders">Purchase orders</TabsTrigger>
          <TabsTrigger value="alerts">
            Alerts{alertTotal ? ` (${alertTotal})` : ""}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="stock">
          {stock.isPending ? (
            <Skeleton className="h-64 w-full" />
          ) : stock.isError ? (
            <p className="error-text" role="alert">
              {stock.error.message}
            </p>
          ) : (
            <StockTable
              items={stock.data.items}
              isAdmin={isAdmin}
              onAdjust={setAdjusting}
              onReorder={setReordering}
              onHistory={setHistory}
            />
          )}
        </TabsContent>
        <TabsContent value="orders">
          <OrdersTab capture={capture} />
        </TabsContent>
        <TabsContent value="purchase-orders">
          <PurchaseOrdersTab isAdmin={isAdmin} />
        </TabsContent>
        <TabsContent value="alerts">
          <AlertsTab />
        </TabsContent>
      </Tabs>
      <AdjustDialog row={adjusting} onClose={() => setAdjusting(null)} />
      <ReorderDialog row={reordering} onClose={() => setReordering(null)} />
      <MovementsDrawer row={history} onClose={() => setHistory(null)} />
    </section>
  );
}
