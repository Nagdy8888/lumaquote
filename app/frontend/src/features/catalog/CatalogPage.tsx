import "./catalog.css";
import { lazy, Suspense, useCallback, useState } from "react";
import { BookOpenCheck, Rotate3d, Search } from "lucide-react";
import { useWorkspaceContext } from "@/shared/api/workspace-context";
import { Input } from "@/shared/ui/input";
import { money, Status } from "@/shared/ui/status";
import { DocumentButton } from "@/shared/ui/document-button";
import { SceneBoundary } from "@/features/overview/SceneBoundary";
import { useReducedMotion } from "@/features/showcase/reducedMotion";

const FixtureCanvas = lazy(() => import("./FixtureShowroom"));
const FixtureInspector = lazy(() => import("./FixtureInspector"));
const FixtureView = lazy(() =>
  import("./FixtureShowroom").then((module) => ({
    default: module.FixtureView,
  })),
);

/**
 * Search the actual catalog and inspect original evidence; current source labeling remains explicit.
 * Each product tile also shows a decorative, lazily loaded 3D fixture for its family (one shared
 * canvas). Once that stage is live, each tile also offers "Inspect in 3D", which opens a modal
 * inspector (orbit, light on/off, colour temperature, exploded view). Under reduced motion no 3D
 * chunk or canvas is requested, no inspect button appears and the CSS fixtures remain.
 */
export function CatalogPage() {
  const { data } = useWorkspaceContext();
  const reduced = useReducedMotion();
  const [stage, setStage] = useState(false);
  const [active, setActive] = useState<string | null>(null);
  const stageReady = useCallback((ready: boolean) => setStage(ready), []);
  const [inspecting, setInspecting] = useState<
    (typeof data.products)[number] | null
  >(null);
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
      {!reduced && (
        <SceneBoundary fallback={null}>
          <Suspense fallback={null}>
            <FixtureCanvas onReady={stageReady} paused={inspecting !== null} />
          </Suspense>
        </SceneBoundary>
      )}
      <div className="catalog-grid" data-stage={stage ? "on" : undefined}>
        {products.map((p, index) => (
          <article
            className="catalog-product"
            key={p.id}
            onPointerEnter={() => setActive(p.id)}
            onPointerLeave={() => setActive(null)}
            onFocus={() => setActive(p.id)}
            onBlur={() => setActive(null)}
          >
            <div
              className={`catalog-product-visual family-${p.sku.slice(0, 2).toLowerCase()}`}
            >
              <div className="fixture-model">
                <span />
                <span />
              </div>
              {!reduced && (
                <SceneBoundary fallback={null}>
                  <Suspense fallback={null}>
                    <FixtureView
                      family={p.sku.slice(0, 2).toLowerCase()}
                      index={index}
                      active={active === p.id}
                    />
                  </Suspense>
                </SceneBoundary>
              )}
              <span>{p.family}</span>
              {stage && (
                <button
                  type="button"
                  className="inspect-button"
                  aria-label={`Inspect ${p.sku} in 3D`}
                  onClick={() => setInspecting(p)}
                >
                  <Rotate3d />
                  Inspect in 3D
                </button>
              )}
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
      {inspecting && (
        <SceneBoundary fallback={null}>
          <Suspense fallback={null}>
            <FixtureInspector
              product={inspecting}
              onClose={() => setInspecting(null)}
            />
          </Suspense>
        </SceneBoundary>
      )}
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
