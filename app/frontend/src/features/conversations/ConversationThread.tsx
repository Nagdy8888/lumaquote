import { useState, type FormEvent } from "react";
import {
  Bot,
  CheckCheck,
  MessageSquareText,
  Send,
  UserRound,
} from "lucide-react";
import type { ConversationDetail } from "@/shared/api/types";
import { customerName } from "@/shared/api/workspace-context";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";
import { Status } from "@/shared/ui/status";
import { useConversationAction } from "./api";

/** Render plain escaped conversation content and explicitly distinguish staff notes from local customer simulations. */
export function ConversationThread({
  detail,
  capture,
}: {
  detail: ConversationDetail;
  capture: boolean;
}) {
  const { conversation, messages } = detail;
  const [text, setText] = useState("");
  const [mode, setMode] = useState("messages");
  const mutation = useConversationAction(conversation.id);
  /** Add a staff note or local-test customer reply; preserve the draft if the server rejects the action. */
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    mutation.mutate(
      { action: mode, body: { text }, key: crypto.randomUUID() },
      {
        /** Clear the composer only after the server confirms the saved message. */
        onSuccess: function clearConfirmedDraft() {
          setText("");
        },
      },
    );
  }
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
                ·{" "}
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
            ? "Automation permitted · Staff approval required"
            : "Staff is in control · Automation paused"}
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
                    ? "Staff note"
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
      </div>
      <form className="composer" onSubmit={submit}>
        <div className="composer-mode">
          <MessageSquareText />
          <label className="sr-only" htmlFor="reply-mode">
            Reply mode
          </label>
          <select
            id="reply-mode"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
          >
            <option value="messages">Internal staff note</option>
            {conversation.channel === "local_test" && (
              <option value="customer-reply">
                Simulate customer reply · local test
              </option>
            )}
          </select>
        </div>
        <Textarea
          aria-label={
            mode === "messages"
              ? "Internal staff note"
              : "Local test customer reply"
          }
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={
            mode === "messages"
              ? "Add a note for your team…"
              : "Enter the customer’s clarification…"
          }
          maxLength={8000}
          rows={3}
        />
        <div className="composer-footer">
          <span>
            {mode === "messages"
              ? "Visible to your team. Not sent externally."
              : "Test reply. No real customer is contacted."}
          </span>
          <Button
            type="submit"
            size="sm"
            disabled={mutation.isPending || !text.trim()}
          >
            <Send data-icon="inline-start" />
            {mode === "messages" ? "Add note" : "Add test reply"}
          </Button>
        </div>
        {mutation.isError && (
          <p className="error-text" role="alert">
            {mutation.error.message}
          </p>
        )}
      </form>
    </section>
  );
}
