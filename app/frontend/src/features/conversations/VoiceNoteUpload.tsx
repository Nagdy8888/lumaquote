import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { request } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";

/** Accept a labeled local-test recording; retain its bytes, operation identity and version on uncertain failures. */
export function VoiceNoteUpload({
  id,
  version,
}: {
  id: string;
  version: number;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [selection, setSelection] = useState<{
    file: File;
    key: string;
    version: number;
  } | null>(null);
  const [validation, setValidation] = useState("");
  const client = useQueryClient();
  const mutation = useMutation({
    /** Send bounded binary data; request replay remains bound to the captured file and conversation version. */
    mutationFn: async function upload() {
      if (!selection) throw new Error("Choose a recording first.");
      return request(
        `/conversations/${id}/audio`,
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
    if (!file.size || file.size > 10 * 1024 * 1024) {
      setSelection(null);
      setValidation("Choose a nonempty recording no larger than 10 MB.");
      return;
    }
    setSelection({ file, key: crypto.randomUUID(), version });
  }
  /** Keep upload initiation explicit; no microphone permission or automatic external processing is requested by file selection. */
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <form className="voice-note-upload" onSubmit={submit}>
      <label htmlFor={`voice-${id}`}>Test customer voice note</label>
      <p>
        English recording · up to 10 MB / 120 seconds. Transcription uses OpenAI
        when enabled.
      </p>
      <Input
        ref={input}
        id={`voice-${id}`}
        type="file"
        accept="audio/*"
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
          ? "Uploading voice note…"
          : "Upload test voice note"}
      </Button>
      {(validation || mutation.error) && (
        <p role="alert" className="error-text">
          {validation || mutation.error?.message}
        </p>
      )}
    </form>
  );
}
