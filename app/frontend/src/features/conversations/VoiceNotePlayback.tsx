import { useEffect, useRef, useState } from "react";
import { documentUrl } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";

/** Load private normalized audio only on staff request; revoke temporary capabilities on navigation or replacement. */
export function VoiceNotePlayback({ id }: { id: string }) {
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
      const value = await documentUrl(`/media/${id}/audio`);
      if (mounted.current) setUrl(value);
      else URL.revokeObjectURL(value);
    } catch (failure) {
      if (mounted.current)
        setError(
          failure instanceof Error
            ? failure.message
            : "Audio could not be loaded.",
        );
    } finally {
      if (mounted.current) setPending(false);
    }
  }
  return (
    <div className="voice-note-playback">
      {url ? (
        <audio
          controls
          preload="metadata"
          src={url}
          aria-label="Voice note audio"
        />
      ) : (
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={pending}
          onClick={load}
        >
          {pending ? "Loading audio…" : "Listen to voice note"}
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
