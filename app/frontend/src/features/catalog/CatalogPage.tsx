import "./catalog.css";
import { useState } from "react";
import { BookOpenCheck, Search } from "lucide-react";
import { useWorkspaceContext } from "@/shared/api/workspace-context";
import { Input } from "@/shared/ui/input";
import { money, Status } from "@/shared/ui/status";
import { DocumentButton } from "@/shared/ui/document-button";

/** Search the actual catalog and inspect original evidence; current source labeling remains explicit. */
export function CatalogPage() {
  const { data } = useWorkspaceContext();
  const [search, setSearch] = useState("");
  const [family, setFamily] = useState("All families");
  const families = [...new Set(data.products.map((p) => p.family))];
  const products = data.products.filter(
    (p) =>
      (family === "All families" || p.family === family) &&
      `${p.sku} ${p.name} ${p.description}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>Evidence behind every recommendation.</h1>
          <p>
            {data.products.length} fictional products. Original catalog pages.
            Explicit price and stock snapshots.
          </p>
        </div>
        <BookOpenCheck />
      </div>
      <div className="catalog-toolbar">
        <div className="search-field">
          <Search />
          <Input
            aria-label="Search product catalog"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by model, product, or specification…"
          />
        </div>
        <select
          aria-label="Product family"
          value={family}
          onChange={(e) => setFamily(e.target.value)}
        >
          <option>All families</option>
          {families.map((f) => (
            <option key={f}>{f}</option>
          ))}
        </select>
        <span>{products.length} products</span>
      </div>
      <div className="catalog-grid">
        {products.map((p) => (
          <article className="catalog-product" key={p.id}>
            <div
              className={`catalog-product-visual family-${p.sku.slice(0, 2).toLowerCase()}`}
            >
              <div className="fixture-model">
                <span />
                <span />
              </div>
              <span>{p.family}</span>
            </div>
            <div className="catalog-product-info">
              <div>
                <strong>{p.sku}</strong>
                <span>{money(p.price)}</span>
              </div>
              <h2>{p.name}</h2>
              <p>
                {p.lumens.toLocaleString()} lm · {p.ip_rating} · {p.cct}K
              </p>
              <div className="catalog-product-bottom">
                {p.discontinued ? (
                  <Status value="Discontinued" />
                ) : (
                  <span
                    className={p.available ? "stock-label" : "out-of-stock"}
                  >
                    {p.available ? `${p.available} available` : "Out of stock"}
                  </span>
                )}
                <DocumentButton
                  path={`/sources/${p.source_id}/pdf`}
                  title={`${p.sku} · Original catalog`}
                  label="Evidence"
                  page={p.page}
                />
              </div>
            </div>
          </article>
        ))}
      </div>
      {products.length === 0 && (
        <p className="empty-copy">
          No products match those filters. Try another model or family.
        </p>
      )}
      <p className="form-footnote">
        Synthetic commercial data. A live quotation requires a validated Google
        Sheets snapshot.
      </p>
    </section>
  );
}
