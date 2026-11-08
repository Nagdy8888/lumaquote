import { useState } from "react";
import { History, Search } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import type { StockRow } from "./api";
import { StockChip, stockState } from "./StatusChip";

type Filter = "all" | "ok" | "low" | "out";

/**
 * The stock table: SKU, name, family, on hand, reserved, available, reorder level and a status chip.
 * Inputs: `items` (server rows), `isAdmin` (shows Adjust and Reorder level; the server still
 * enforces the role), and three row callbacks. Local state is only the text search (SKU, name,
 * family) and the status filter; filtering never changes quantities. Every number is the server's.
 */
export function StockTable({
  items,
  isAdmin,
  onAdjust,
  onReorder,
  onHistory,
}: {
  items: StockRow[];
  isAdmin: boolean;
  onAdjust: (row: StockRow) => void;
  onReorder: (row: StockRow) => void;
  onHistory: (row: StockRow) => void;
}) {
  const [text, setText] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const needle = text.trim().toLowerCase();
  const rows = items.filter(
    (row) =>
      (filter === "all" || stockState(row) === filter) &&
      `${row.sku} ${row.name} ${row.family}`.toLowerCase().includes(needle),
  );
  return (
    <div className="inv-panel">
      <div className="inv-filters">
        <div className="search-field">
          <Search />
          <Input
            aria-label="Search stock by SKU, name or family"
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Search SKU, name or family…"
          />
        </div>
        <select
          aria-label="Filter by stock status"
          value={filter}
          onChange={(event) => setFilter(event.target.value as Filter)}
        >
          <option value="all">All statuses</option>
          <option value="ok">OK</option>
          <option value="low">Low</option>
          <option value="out">Out</option>
        </select>
        <span className="inv-count" role="status">
          {rows.length} of {items.length} products
        </span>
      </div>
      <div className="inv-scroll">
        <table className="inv-table">
          <caption className="sr-only">Stock by product</caption>
          <thead>
            <tr>
              <th scope="col">SKU</th>
              <th scope="col">Name</th>
              <th scope="col">Family</th>
              <th scope="col" className="num">
                On hand
              </th>
              <th scope="col" className="num">
                Reserved
              </th>
              <th scope="col" className="num">
                Available
              </th>
              <th scope="col" className="num">
                Reorder level
              </th>
              <th scope="col">Status</th>
              <th scope="col">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.product_id}>
                <th scope="row" className="inv-sku">
                  {row.sku}
                </th>
                <td>{row.name}</td>
                <td>{row.family}</td>
                <td className="num">{row.on_hand}</td>
                <td className="num">{row.reserved}</td>
                <td className="num">
                  <strong>{row.available}</strong>
                </td>
                <td className="num">{row.reorder_level}</td>
                <td>
                  <StockChip state={stockState(row)} />
                </td>
                <td className="inv-actions">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onHistory(row)}
                    aria-label={`Movement history for ${row.sku}`}
                  >
                    <History data-icon="inline-start" />
                    History
                  </Button>
                  {isAdmin && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onAdjust(row)}
                        aria-label={`Adjust stock for ${row.sku}`}
                      >
                        Adjust
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onReorder(row)}
                        aria-label={`Set reorder level for ${row.sku}`}
                      >
                        Reorder level
                      </Button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <p className="empty-copy">No products match this search.</p>
        )}
      </div>
    </div>
  );
}
