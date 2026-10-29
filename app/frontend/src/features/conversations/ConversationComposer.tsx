import { useState, type FormEvent } from "react";
import { Send } from "lucide-react";
import type { Conversation } from "@/shared/api/types";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";
import { ToggleGroup, ToggleGroupItem } from "@/shared/ui/toggle-group";
import { useConversationAction, type ConversationCommand } from "./api";

/** Keep internal notes, authorized human customer replies, and local test simulations explicit and separate. */
export function ConversationComposer({
  conversation,
}: {
  conversation: Conversation;
}) {
  const [text, setText] = useState("");
  const [mode, setMode] = useState<"messages" | "reply" | "customer-reply">(
    "messages",
  );
  const mutation = useConversationAction(conversation.id);
  const labels = {
    messages: "Internal staff note",
    reply: "Customer reply",
    "customer-reply": "Local test customer reply",
  };
  /** Accept only the declared composition modes; switching modes never grants the corresponding server permission. */
  function selectMode(value: string) {
    if (value === "messages" || value === "reply" || value === "customer-reply")
      setMode(value);
  }
  /** Queue a human reply only under current takeover, or persist the explicitly selected internal/local-test action. */
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    const command: ConversationCommand =
      mode === "reply"
        ? {
            action: "reply",
            body: { text, expected_version: conversation.version },
            key: crypto.randomUUID(),
          }
        : { action: mode, body: { text }, key: crypto.randomUUID() };
    mutation.mutate(command, {
      /** Clear composition only after the persisted result and query reconciliation are confirmed. */
      onSuccess: function clearConfirmedDraft() {
        setText("");
      },
    });
  }
  return (
    <form className="composer" onSubmit={submit}>
      <div className="composer-mode">
        <ToggleGroup
          type="single"
          value={mode}
          onValueChange={selectMode}
          variant="outline"
          size="sm"
          aria-label="Message destination"
        >
          <ToggleGroupItem
            value="messages"
            aria-label="Internal staff note mode"
          >
            Staff note
          </ToggleGroupItem>
          <ToggleGroupItem
            value="reply"
            aria-label="Customer reply mode"
            disabled={conversation.owner !== "staff"}
          >
            Reply
          </ToggleGroupItem>
          {conversation.channel === "local_test" && (
            <ToggleGroupItem
              value="customer-reply"
              aria-label="Local test customer reply mode"
            >
              Test reply
            </ToggleGroupItem>
          )}
        </ToggleGroup>
      </div>
      <Textarea
        aria-label={labels[mode]}
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder={
          mode === "messages"
            ? "Add a note for your team…"
            : mode === "reply"
              ? "Ask the customer a question…"
              : "Enter the customer’s clarification…"
        }
        maxLength={mode === "reply" ? 2000 : 8000}
        rows={3}
      />
      <div className="composer-footer">
        <span>
          {mode === "messages"
            ? "Internal only. Take over to reply to the customer."
            : mode === "reply"
              ? conversation.channel === "local_test"
                ? "Queues a reply in the local test channel."
                : "Queues a WhatsApp reply as your sales team."
              : "Simulated customer input. No real customer is contacted."}
        </span>
        <Button
          type="submit"
          size="sm"
          disabled={
            mutation.isPending ||
            !text.trim() ||
            (mode === "reply" && conversation.owner !== "staff")
          }
        >
          <Send data-icon="inline-start" />
          {mode === "messages"
            ? "Add note"
            : mode === "reply"
              ? "Queue customer reply"
              : "Add test reply"}
        </Button>
      </div>
      {mutation.isError && (
        <p className="error-text" role="alert">
          {mutation.error.message}
        </p>
      )}
    </form>
  );
}
