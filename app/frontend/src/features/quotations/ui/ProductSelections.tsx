import { useState } from "react";
import { BookOpenCheck, Plus, Trash2 } from "lucide-react";
import type { Product } from "@/shared/api/types";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { DocumentButton } from "@/shared/ui/document-button";
import { money } from "@/shared/ui/status";
import type { EditableLine } from "../useQuotationDraft";
/** Own catalog selection and quantity editing; forward unsaved values without inventing authoritative totals. */
export function ProductSelections({
  lines,
  products,
  onChange,
}: {
  lines: EditableLine[];
  products: Product[];
  onChange: (value: EditableLine[]) => void;
}) {
  const [selected, setSelected] = useState("");
  const available = products.filter(
    (p) =>
      !p.discontinued &&
      p.available > 0 &&
      !lines.some((line) => line.product_id === p.id),
  );
  /** Add a selected authoritative SKU using its pack size, with actual stock validation deferred to the backend. */
  function addProduct() {
    const p = products.find((product) => product.id === selected);
    if (p) {
      onChange([...lines, { product_id: p.id, quantity: p.pack_size }]);
      setSelected("");
    }
  }
  return (
    <>
      <div className="quote-lines">
        {lines.map((line, index) => {
          const p = products.find((product) => product.id === line.product_id);
          return (
            <div className="quote-line" key={line.product_id}>
              <div className="line-heading">
                <span className="product-thumb">
                  <span />
                </span>
                <div>
                  <strong>{p?.sku ?? "Product unavailable"}</strong>
                  <span>{p?.name}</span>
                </div>
                <button
                  className="icon-button"
                  aria-label={`Remove ${p?.sku ?? "product"}`}
                  onClick={() => {
                    onChange(lines.filter((_, i) => i !== index));
                  }}
                >
                  <Trash2 />
                </button>
              </div>
              <div className="line-commercial">
                <label>
                  Quantity
                  <Input
                    aria-label={`Quantity for ${p?.sku}`}
                    type="number"
                    min={p?.pack_size ?? 1}
                    step={p?.pack_size ?? 1}
                    max={10000}
                    value={line.quantity}
                    onChange={(event) => {
                      onChange(
                        lines.map((value, i) =>
                          i === index
                            ? {
                                ...value,
                                quantity: Number(event.target.value),
                              }
                            : value,
                        ),
                      );
                    }}
                  />
                </label>
                <div>
                  <span>Unit price</span>
                  <strong>{p ? money(p.price) : "—"}</strong>
                </div>
                <span className="stock-label">
                  {p?.available ?? 0} available
                </span>
              </div>
              <div className="line-evidence">
                <BookOpenCheck />
                <span>Catalog evidence · Page {p?.page ?? 1}</span>
                {p && (
                  <DocumentButton
                    path={`/sources/${p.source_id}/pdf`}
                    title={`${p.sku} · Original catalog`}
                    label="View"
                    page={p.page}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="add-product">
        <label className="sr-only" htmlFor="product-selection">
          Choose catalog product
        </label>
        <select
          id="product-selection"
          value={selected}
          onChange={(event) => setSelected(event.target.value)}
        >
          <option value="">Choose a product…</option>
          {available.map((p) => (
            <option key={p.id} value={p.id}>
              {p.sku} · {p.name}
            </option>
          ))}
        </select>
        <Button
          variant="outline"
          size="icon"
          aria-label="Add selected product"
          onClick={addProduct}
          disabled={!selected}
        >
          <Plus />
        </Button>
      </div>
    </>
  );
}
