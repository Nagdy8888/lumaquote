import "./conversations.css";
import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, MessageSquareText } from "lucide-react";
import { request } from "@/shared/api/client";
import type { Conversation } from "@/shared/api/types";
import { Field, FieldGroup, FieldLabel } from "@/shared/ui/field";
import { Input } from "@/shared/ui/input";
import { Textarea } from "@/shared/ui/textarea";
import { Button } from "@/shared/ui/button";

/** Create an explicitly local-test request through the same server workflow used by channel adapters. */
export function NewRequest() {
  const navigate = useNavigate();
  const client = useQueryClient();
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [text, setText] = useState("");
  const [key] = useState(() => crypto.randomUUID());
  const mutation = useMutation({
    /** A stable form identity makes a retry after an unknown network result safe. */
    mutationFn: function createRequest() {
      return request<Conversation>(
        "/conversations",
        {
          method: "POST",
          body: JSON.stringify({
            customer_name: name,
            customer_company: company,
            text,
          }),
        },
        key,
      );
    },
    /** Open the persisted request only after its server-created identity is confirmed. */
    onSuccess: function openRequest(result) {
      void client.invalidateQueries({ queryKey: ["workspace"] });
      navigate(`/inbox/${result.id}`);
    },
  });
  /** Submit once through the mutation so pending, errors, and canonical navigation remain consistent. */
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <section className="new-request">
      <Link className="back-link" to="/inbox">
        <ArrowLeft />
        Back to inbox
      </Link>
      <div className="page-heading">
        <div>
          <h1>Start with a conversation.</h1>
          <p>Add a customer request to the local test channel.</p>
        </div>
        <MessageSquareText />
      </div>
      <form onSubmit={submit}>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="customer-name">Customer name</FieldLabel>
            <Input
              id="customer-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={120}
              required
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="customer-company">Company</FieldLabel>
            <Input
              id="customer-company"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              maxLength={160}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="request-text">Customer request</FieldLabel>
            <Textarea
              id="request-text"
              rows={6}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="For example: Please quote 24 DL-002 downlights for our new studio."
              maxLength={8000}
              required
            />
          </Field>
          {mutation.isError && (
            <p role="alert" className="error-text">
              {mutation.error.message}
            </p>
          )}
          <Button size="lg" disabled={mutation.isPending} type="submit">
            {mutation.isPending ? "Creating request…" : "Create local request"}
            <ArrowRight data-icon="inline-end" />
          </Button>
        </FieldGroup>
      </form>
      <p className="form-footnote">
        This does not contact a real customer. Telegram and WhatsApp requests
        will appear here once a test connection is configured.
      </p>
    </section>
  );
}
