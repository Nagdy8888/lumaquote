import { useEffect, useRef, useState } from "react";
import { documentUrl } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";

/**
 * Fetch a normalized private attachment only after an explicit staff request.
 * The API authorizes message/kind and returns bytes; no Storage URL is exposed.
 * This owner revokes blob capabilities on replacement/unmount, including a fetch
 * that resolves after navigation. Preview availability does not establish that
 * its transcript/label fields are confirmed or safe to quote.
 */
export function MediaPreview({
  id,
  kind,
}: {
  id: string;
  kind: "audio" | "image";
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const mounted = useRef(true);
  /** Prevent a delayed fetch from retaining a private object URL after navigation. */
  useEffect(
    /** Own the playback request lifetime so navigation cannot retain a private capability. */ function ownLifetime() {
      mounted.current = true;
      /** Mark this playback owner unavailable before an outstanding request completes. */
      return function releaseOwner() {
        mounted.current = false;
      };
    },
    [],
  );
  /** Revoke the current browser-local audio capability when its owner changes or unmounts. */
  useEffect(
    /** Bind cleanup to the currently displayed audio object URL. */
    function ownUrl() {
      /** Release the captured URL without affecting another message's playback. */
      return function releaseUrl() {
        if (url) URL.revokeObjectURL(url);
      };
    },
    [url],
  );
  /** Fetch authorized bytes through the API; never expose a Storage path or persistent public URL. */
  async function load() {
    setPending(true);
    setError("");
    try {
      const value = await documentUrl(`/media/${id}/${kind}`);
      if (mounted.current) setUrl(value);
      else URL.revokeObjectURL(value);
    } catch (failure) {
      if (mounted.current)
        setError(
          failure instanceof Error
            ? failure.message
            : "Attachment could not be loaded.",
        );
    } finally {
      if (mounted.current) setPending(false);
    }
  }
  return (
    <div className="media-preview">
      {url ? (
        kind === "image" ? (
          <img src={url} alt="Unconfirmed product-label photo" />
        ) : (
          <audio
            controls
            preload="metadata"
            src={url}
            aria-label="Voice note audio"
          />
        )
      ) : (
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={pending}
          onClick={load}
        >
          {pending
            ? "Loading attachment…"
            : kind === "image"
              ? "View label photo"
              : "Listen to voice note"}
        </Button>
      )}
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
    </div>
  );
}
