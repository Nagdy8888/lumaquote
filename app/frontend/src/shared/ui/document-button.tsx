import { useEffect, useRef, useState } from "react";
import { FileText, X } from "lucide-react";
import { documentUrl } from "@/shared/api/client";
import { Button } from "./button";

/** Fetch an authorized document into a native focus-managed dialog and release its temporary URL when closed. */
export function DocumentButton({
  path,
  title,
  label = "View PDF",
  page = 1,
}: {
  path: string;
  title: string;
  label?: string;
  page?: number;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  /** Release the blob capability whenever a document is replaced or its owning component unmounts. */
  useEffect(
    /** Release the current private blob URL when it changes or its owner unmounts. */
    function manageDocumentUrl() {
      /** Revoke the temporary document capability if one was created. */
      function releaseUrl() {
        if (url) URL.revokeObjectURL(url);
      }
      return releaseUrl;
    },
    [url],
  );
  /** Fetch through authenticated API access; expose no raw Storage path or provider bearer token. */
  async function openDocument() {
    setPending(true);
    setError("");
    try {
      const value = await documentUrl(path);
      setUrl(value);
      dialog.current?.showModal();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Document could not be loaded.",
      );
    } finally {
      setPending(false);
    }
  }
  /** Close the native modal and immediately drop the local document capability. */
  function closeDocument() {
    dialog.current?.close();
    setUrl(null);
  }
  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={pending}
        onClick={openDocument}
      >
        <FileText data-icon="inline-start" />
        {pending ? "Loading PDF…" : label}
      </Button>
      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
      <dialog
        className="document-dialog"
        ref={dialog}
        aria-label={title}
        onClose={() => setUrl(null)}
      >
        <header>
          <h2>{title}</h2>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Close document"
            onClick={closeDocument}
          >
            <X />
          </Button>
        </header>
        {url && <iframe title={title} src={`${url}#page=${page}&view=FitH`} />}
      </dialog>
    </>
  );
}
