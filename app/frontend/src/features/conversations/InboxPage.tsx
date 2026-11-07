import "./conversations.css";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Inbox, Search } from "lucide-react";
import {
  customerName,
  useWorkspaceContext,
} from "@/shared/api/workspace-context";
import { captureText } from "@/shared/lib/mask";
import { Input } from "@/shared/ui/input";
import { Status } from "@/shared/ui/status";
import { Skeleton } from "@/shared/ui/skeleton";
import { useConversation } from "./api";
import { ConversationThread } from "./ConversationThread";
import { SectionSwitch, type InboxSection } from "./SectionSwitch";
import { QuotationPanel } from "@/features/quotations/QuotationPanel";

/** Compose request navigation, conversation, and quotation review as independent focused feature components. */
export function InboxPage() {
  const { data, capture } = useWorkspaceContext();
  const { id } = useParams();
  const [search, setSearch] = useState("");
  const selected = id ?? data.conversations[0]?.id;
  const detail = useConversation(selected);
  const [chosen, setChosen] = useState<{ id?: string; value: InboxSection }>({
    value: "conversation",
  });
  // Portrait only: the choice belongs to one conversation, so another selection starts on "Conversation".
  const section: InboxSection =
    chosen.id === selected ? chosen.value : "conversation";
  const requests = data.conversations.filter((c) =>
    `${c.customer_name} ${c.customer_company} ${c.preview}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );
  return (
    <div className="inbox-page">
      <div className="page-heading">
        <div>
          <h1>Conversations, with context.</h1>
          <p>From the first question to the quotation you can stand behind.</p>
        </div>
        <span className="page-count">
          {data.conversations.length}{" "}
          {data.conversations.length === 1 ? "conversation" : "conversations"}
        </span>
      </div>
      <div className="inbox-workspace" data-section={section}>
        <aside className="conversation-sidebar" aria-label="Conversation list">
          <div className="conversation-sidebar-title">
            <h2>Inbox</h2>
            <span>{requests.length}</span>
          </div>
          <div className="search-field">
            <Search />
            <Input
              aria-label="Search conversations"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search requests…"
            />
          </div>
          <nav aria-label="Customer conversations">
            {requests.map((c) => (
              <Link
                key={c.id}
                to={`/inbox/${c.id}`}
                className={`conversation-item${c.id === selected ? " selected" : ""}`}
              >
                <div className="conversation-item-top">
                  <strong>
                    {capture
                      ? "Commercial customer"
                      : c.customer_company || c.customer_name}
                  </strong>
                  <time>
                    {new Date(c.updated_at).toLocaleTimeString("en-US", {
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </time>
                </div>
                <span>{customerName(c.customer_name, capture)}</span>
                <p>
                  {c.preview
                    ? captureText(c.preview, capture)
                    : "New customer request"}
                </p>
                <Status value={c.status} />
              </Link>
            ))}
          </nav>
          {requests.length === 0 && (
            <p className="empty-copy">No requests match your search.</p>
          )}
        </aside>
        {detail.isPending && selected ? (
          <div className="inbox-loading">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        ) : detail.isError ? (
          <div className="empty-copy" role="alert">
            {detail.error.message}
          </div>
        ) : detail.data ? (
          <>
            <SectionSwitch
              value={section}
              onChange={(value) => setChosen({ id: selected, value })}
              needsApproval={detail.data.quote?.status === "review"}
            />
            <ConversationThread
              key={`thread:${selected}`}
              detail={detail.data}
              capture={capture}
              jobs={data.jobs.filter((job) => job.conversation_id === selected)}
            />
            <QuotationPanel
              key={`quotation:${selected}`}
              detail={detail.data}
              products={data.products}
              role={data.role}
            />
          </>
        ) : (
          <div className="inbox-empty">
            <Inbox />
            <h2>Your next conversation starts here.</h2>
            <p>
              Create a local request or connect Telegram or WhatsApp to receive requests.
            </p>
            <Link to="/requests/new">Create your first request</Link>
          </div>
        )}
      </div>
    </div>
  );
}
