import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { request } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/shared/ui/toggle-group";

/**
 * Accept explicit local-test audio/image uploads without granting media authority.
 * Capture file, kind, operation UUID and displayed version at selection; failed
 * retries retain that tuple even when polling updates the conversation. A kind
 * change clears it deliberately. Success clears the selection only after server
 * acceptance and reconciles detail/workspace caches. Client size checks improve
 * feedback; server byte/decode/admission checks remain authoritative.
 */
export function MediaUpload({ id, version }: { id: string; version: number }) {
  const input = useRef<HTMLInputElement>(null);
  const [kind, setKind] = useState<"audio" | "image">("audio");
  const maximum = kind === "audio" ? 10 : 5;
  const label =
    kind === "audio"
      ? "Test customer voice note"
      : "Test customer product-label photo";
  const [selection, setSelection] = useState<{
    file: File;
    key: string;
    version: number;
    kind: "audio" | "image";
  } | null>(null);
  const [validation, setValidation] = useState("");
  const client = useQueryClient();
  const mutation = useMutation({
    /** Send bounded binary data; request replay remains bound to the captured file and conversation version. */
    mutationFn: async function upload() {
      if (!selection) throw new Error("Choose an attachment first.");
      return request(
        `/conversations/${id}/${selection.kind}`,
        {
          method: "POST",
          body: selection.file,
          headers: {
            "Content-Type": "application/octet-stream",
            "Expected-Version": String(selection.version),
          },
        },
        selection.key,
      );
    },
    /** Clear only the confirmed upload and await canonical detail/aggregate reconciliation. */
    onSuccess: async function reconcile() {
      setSelection(null);
      if (input.current) input.current.value = "";
      await Promise.all([
        client.invalidateQueries({ queryKey: ["conversation"] }),
        client.invalidateQueries({ queryKey: ["workspace"] }),
      ]);
    },
  });
  /** Capture the current version once with the selected file; background refresh cannot silently change its precondition. */
  function choose(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    mutation.reset();
    setValidation("");
    if (!file) {
      setSelection(null);
      return;
    }
    if (!file.size || file.size > maximum * 1024 * 1024) {
      setSelection(null);
      setValidation(
        `Choose a nonempty attachment no larger than ${maximum} MB.`,
      );
      return;
    }
    setSelection({ file, key: crypto.randomUUID(), version, kind });
  }
  /** Change attachment type explicitly and release the previous selection/precondition before accepting different bytes. */
  function changeKind(value: string) {
    if (value !== "audio" && value !== "image") return;
    setKind(value);
    setSelection(null);
    setValidation("");
    mutation.reset();
    if (input.current) input.current.value = "";
  }
  /** Keep upload initiation explicit; no microphone permission or automatic external processing is requested by file selection. */
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <form className="media-upload" onSubmit={submit}>
      <ToggleGroup
        type="single"
        value={kind}
        onValueChange={changeKind}
        disabled={mutation.isPending}
        aria-label="Customer attachment type"
      >
        <ToggleGroupItem value="audio" aria-label="Voice note attachment">
          Voice note
        </ToggleGroupItem>
        <ToggleGroupItem
          value="image"
          aria-label="Product-label photo attachment"
        >
          Label photo
        </ToggleGroupItem>
      </ToggleGroup>
      <label htmlFor={`media-${id}`}>{label}</label>
      <p>
        {kind === "audio"
          ? "English recording, up to 10 MB / 120 seconds. Transcription uses OpenAI when enabled."
          : "JPEG, PNG or WebP, up to 5 MB. Label reading uses OpenAI when enabled; written field confirmation is required."}
      </p>
      <Input
        ref={input}
        id={`media-${id}`}
        type="file"
        accept={
          kind === "audio" ? "audio/*" : "image/jpeg,image/png,image/webp"
        }
        disabled={mutation.isPending}
        onChange={choose}
      />
      <Button
        type="submit"
        variant="outline"
        size="sm"
        disabled={!selection || mutation.isPending}
      >
        {mutation.isPending
          ? "Uploading attachment?"
          : kind === "audio"
            ? "Upload test voice note"
            : "Upload test label photo"}
      </Button>
      {(validation || mutation.error) && (
        <p role="alert" className="error-text">
          {validation || mutation.error?.message}
        </p>
      )}
    </form>
  );
}
