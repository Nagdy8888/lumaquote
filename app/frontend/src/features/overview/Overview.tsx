import "./overview.css";
import { lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  FileCheck2,
  MessageSquareText,
  ShieldCheck,
} from "lucide-react";
import {
  customerName,
  useWorkspaceContext,
} from "@/shared/api/workspace-context";
import { captureText } from "@/shared/lib/mask";
import { Status, money } from "@/shared/ui/status";
import { Button } from "@/shared/ui/button";
import { LightingFallback, SceneBoundary } from "./SceneBoundary";

const LightingScene = lazy(() => import("./LightingScene"));

/** Show actual request state and a domain-specific lighting scene without inventing business impact metrics. */
export function Overview() {
  const { data, capture } = useWorkspaceContext();
  const awaiting = data.quotes.filter((q) => q.status === "review").length;
  const quoted = data.conversations.filter((c) => c.status === "quoted").length;
  const running = data.jobs.filter((job) => job.status === "running").length;
  const attention = data.conversations.filter(
    (c) => c.status === "needs_staff",
  ).length;
  return (
    <div className="overview">
      <div className="page-heading">
        <div>
          <h1>A clearer path to every quote.</h1>
          <p>
            Your conversations, product evidence, and next decisions. In one
            place.
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link to="/inbox">
            Open inbox
            <ArrowUpRight data-icon="inline-end" />
          </Link>
        </Button>
      </div>
      <section className="lighting-hero">
        <div className="hero-copy">
          <h2>
            Good conversations.
            <br />
            Brilliant outcomes.
          </h2>
          <p>
            Turn a customer's brief into a considered quotation—with the
            evidence behind it and your team's approval on it.
          </p>
          <Link to="/inbox">
            Review your workspace
            <ArrowRight />
          </Link>
          <div className="hero-assurance">
            <ShieldCheck />
            Your team approves. Then it goes.
          </div>
        </div>
        <div className="hero-scene">
          <SceneBoundary>
            <Suspense fallback={<LightingFallback />}>
              <LightingScene />
            </Suspense>
          </SceneBoundary>
        </div>
      </section>
      <section
        className="metric-strip"
        aria-label="Actual stored request counts"
      >
        <div>
          <span>Open conversations</span>
          <strong>
            {data.conversations
              .filter((c) => c.status !== "quoted")
              .length.toString()
              .padStart(2, "0")}
          </strong>
          <small>Customer requests in your workspace</small>
        </div>
        <div>
          <span>Ready for review</span>
          <strong>{awaiting.toString().padStart(2, "0")}</strong>
          <small>Quotations waiting for your decision</small>
        </div>
        <div>
          <span>Quotation ready</span>
          <strong>{quoted.toString().padStart(2, "0")}</strong>
          <small>Completed local quotation workflows</small>
        </div>
        <div>
          <span>Needs attention</span>
          <strong>{attention.toString().padStart(2, "0")}</strong>
          <small>Requests requiring a human judgment</small>
        </div>
        <div>
          <span>Assistant jobs running</span>
          <strong>{running.toString().padStart(2, "0")}</strong>
          <small>Among the 20 newest jobs</small>
        </div>
      </section>
      <div className="overview-lower">
        <section className="request-section">
          <div className="section-heading">
            <h2>On your sales desk</h2>
            <Link to="/inbox">
              View all
              <ArrowUpRight />
            </Link>
          </div>
          <div className="request-table">
            <div className="request-table-head">
              <span>Customer & request</span>
              <span>Status</span>
              <span>Channel</span>
              <span />
            </div>
            {data.conversations.slice(0, 5).map((c) => (
              <Link
                className="request-table-row"
                to={`/inbox/${c.id}`}
                key={c.id}
              >
                <div className="request-person">
                  <div className="avatar">
                    {capture
                      ? "PC"
                      : c.customer_name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                  </div>
                  <div>
                    <strong>
                      {capture
                        ? "Commercial customer"
                        : c.customer_company || c.customer_name}
                    </strong>
                    <small>
                      {customerName(c.customer_name, capture)} ·{" "}
                      {captureText(c.preview ?? "", capture).slice(0, 62)}
                    </small>
                  </div>
                </div>
                <Status value={c.status} />
                <span className="channel-label">
                  <MessageSquareText />
                  {c.channel === "local_test"
                    ? "Local test"
                    : c.channel === "telegram"
                      ? "Telegram"
                      : c.channel === "email"
                        ? "Email"
                        : "WhatsApp"}
                </span>
                <ArrowUpRight />
              </Link>
            ))}
            {data.conversations.length === 0 && (
              <p className="empty-copy">
                Your first customer request starts here. Create a request to
                begin.
              </p>
            )}
          </div>
        </section>
        <section className="workflow-note">
          <div className="section-heading">
            <h2>Considered at every step</h2>
            <ShieldCheck />
          </div>
          <div className="workflow-step">
            <MessageSquareText />
            <div>
              <strong>Understand the request</strong>
              <p>Ask about the details that matter.</p>
            </div>
          </div>
          <div className="workflow-step">
            <FileCheck2 />
            <div>
              <strong>Ground it in evidence</strong>
              <p>Catalog facts. Validated prices and stock.</p>
            </div>
          </div>
          <div className="workflow-step">
            <CheckCircle2 />
            <div>
              <strong>A human has the final word</strong>
              <p>Approve the exact revision before delivery.</p>
            </div>
          </div>
          <div className="workflow-note-footer">
            {data.products.length} catalog products
            <span>USD · Tax excluded</span>
          </div>
        </section>
      </div>
      <section className="recent-activity">
        <div className="section-heading">
          <h2>Latest activity</h2>
          <span>
            {data.activity.length ? "From your audit history" : "A clean slate"}
          </span>
        </div>
        {data.activity.slice(0, 4).map((event) => (
          <div className="activity-row" key={event.id}>
            <span className="activity-dot" />
            <span>
              {event.action.replaceAll(".", " · ").replaceAll("_", " ")}
            </span>
            <time>
              {new Date(event.created_at).toLocaleTimeString("en-US", {
                hour: "numeric",
                minute: "2-digit",
              })}
            </time>
          </div>
        ))}
        {data.activity.length === 0 && (
          <p className="empty-copy">
            As your team works, important decisions and delivery outcomes will
            appear here.
          </p>
        )}
        <span className="allowance-note">
          Estimated / reserved AI usage:{" "}
          {money(data.usage.estimated_or_reserved)}. Provider billing is
          separate.
        </span>
      </section>
    </div>
  );
}
