import { Bot, CheckCheck, UserRound } from "lucide-react";
import type { ConversationDetail } from "@/shared/api/types";
import { customerName } from "@/shared/api/workspace-context";
import { Button } from "@/shared/ui/button";

import { Status } from "@/shared/ui/status";
import { useConversationAction } from "./api";
import { ConversationComposer } from "./ConversationComposer";
import { Alert, AlertTitle, AlertDescription } from "@/shared/ui/alert";

/** Render plain escaped conversation content and explicitly distinguish staff notes from local customer simulations. */
export function ConversationThread({
  detail,
  capture,
}: {
  detail: ConversationDetail;
  capture: boolean;
}) {
  const { conversation, messages } = detail;
  const mutation = useConversationAction(conversation.id);
  /** Pause or explicitly resume automation using the currently displayed optimistic version. */
  function changeOwnership() {
    mutation.mutate({
      action: "ownership",
      body: {
        owner: conversation.owner === "agent" ? "staff" : "agent",
        expected_version: conversation.version,
      },
      key: crypto.randomUUID(),
    });
  }
  return (
    <section className="thread">
      <header className="thread-header">
        <div className="request-person">
          <div className="avatar">
            {capture
              ? "PC"
              : conversation.customer_name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
          </div>
          <div>
            <h2>{customerName(conversation.customer_name, capture)}</h2>
            <p>
              {capture ? "Commercial customer" : conversation.customer_company}{" "}
              <span>
                Â·{" "}
                {conversation.channel === "local_test"
                  ? "Local test channel"
                  : "WhatsApp"}
              </span>
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={changeOwnership}
          disabled={mutation.isPending}
        >
          {conversation.owner === "agent" ? (
            <UserRound data-icon="inline-start" />
          ) : (
            <Bot data-icon="inline-start" />
          )}
          {conversation.owner === "agent" ? "Take over" : "Resume agent"}
        </Button>
      </header>
      <div className="thread-state">
        <span>
          <Bot />
          {conversation.owner === "agent"
            ? "Automation permitted Â· Staff approval required"
            : "Staff is in control Â· Automation paused"}
        </span>
        <Status value={conversation.status} />
      </div>
      <div
        className="message-list"
        aria-live="polite"
        aria-relevant="additions"
      >
        <div className="conversation-date">
          {new Date(conversation.created_at).toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
        </div>
        {messages.map((message) => (
          <article
            key={message.id}
            className={`message message-${message.actor}`}
          >
            <div className="message-label">
              {message.actor === "customer"
                ? customerName(conversation.customer_name, capture)
                : message.actor === "assistant"
                  ? "LumaQuote"
                  : message.actor === "staff"
                    ? message.outbound
                      ? "Sales team"
                      : "Staff note"
                    : "Workflow update"}
              {message.kind !== "text" && (
                <span>
                  {message.kind === "audio"
                    ? "Voice transcript"
                    : message.kind === "image"
                      ? "Product-label photo"
                      : "Quotation document"}
                </span>
              )}
            </div>
            <p>{message.body}</p>
            <div className="message-time">
              <time>
                {new Date(message.created_at).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </time>
              {message.actor === "assistant" && <CheckCheck />}
            </div>
          </article>
        ))}
        {detail.delivery
          .filter(
            (item) =>
              item.kind === "reply" &&
              ["queued", "submitting", "blocked", "failed", "unknown"].includes(
                item.status,
              ),
          )
          .map((item) => (
            <Alert role="status" key={item.id}>
              <AlertTitle>
                Customer reply <Status value={item.status} />
              </AlertTitle>
              <AlertDescription>
                {item.preview ?? "Waiting for a confirmed delivery outcome."}
              </AlertDescription>
            </Alert>
          ))}
      </div>
      <ConversationComposer conversation={conversation} />
    </section>
  );
}
