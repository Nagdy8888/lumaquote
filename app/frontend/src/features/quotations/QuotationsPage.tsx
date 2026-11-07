import "./quotations.css";
import { lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, FileCheck2 } from "lucide-react";
import { useWorkspaceContext } from "@/shared/api/workspace-context";
import { Status, money } from "@/shared/ui/status";
import { DocumentButton } from "@/shared/ui/document-button";
import { SceneBoundary } from "@/features/overview/SceneBoundary";
import { useReducedMotion } from "@/features/showcase/reducedMotion";

const RevisionStack = lazy(() => import("./RevisionStack"));

/**
 * List actual immutable revisions and independent delivery outcomes; previous revisions stay visibly
 * historical. The heading shows a decorative, lazily loaded stack of blank quotation sheets in place
 * of the icon; reduced motion, a missing WebGL context or a failed chunk all keep the static icon.
 */
export function QuotationsPage() {
  const { data, capture } = useWorkspaceContext();
  const reduced = useReducedMotion();
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>Every detail, considered.</h1>
          <p>Your quotation revisions and their delivery outcomes.</p>
        </div>
        {reduced ? (
          <FileCheck2 />
        ) : (
          <SceneBoundary fallback={<FileCheck2 />}>
            <Suspense fallback={<div className="revision-stack" />}>
              <RevisionStack
                sheets={data.quotes.length}
                fallback={<FileCheck2 />}
              />
            </Suspense>
          </SceneBoundary>
        )}
      </div>
      <div className="quote-register">
        <div className="register-head">
          <span>Quotation</span>
          <span>Customer</span>
          <span>Total</span>
          <span>Review & delivery</span>
          <span>Documents</span>
        </div>
        {data.quotes.map((quote) => (
          <article className="register-row" key={quote.id}>
            <Link to={`/inbox/${quote.conversation_id}`}>
              <strong>{quote.number}</strong>
              <small>
                Revision {quote.revision}
                <ArrowUpRight />
              </small>
            </Link>
            <span>
              {capture
                ? "Commercial customer"
                : quote.customer_company || quote.customer_name}
            </span>
            <strong>{money(quote.content.total)}</strong>
            <div>
              <Status value={quote.status} />
              {quote.delivery && <Status value={quote.delivery} />}
            </div>
            {!capture && (
              <DocumentButton
                path={`/quotes/${quote.id}/pdf`}
                title={`${quote.number} · Revision ${quote.revision}`}
              />
            )}
          </article>
        ))}
        {data.quotes.length === 0 && (
          <div className="large-empty">
            <FileCheck2 />
            <h2>A considered offer starts with a request.</h2>
            <p>
              Open a conversation to select products and prepare your first
              quotation.
            </p>
            <Link to="/inbox">Open inbox</Link>
          </div>
        )}
      </div>
    </section>
  );
}
