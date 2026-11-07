import { useEffect, useRef, useState } from "react";
import { computePeaks, formatClock, normalizePeaks } from "./waveform";

const BUCKETS = 64;
const BAR = 3;
const GAP = 2;
const HEIGHT = 32;
const WIDTH = BUCKETS * (BAR + GAP) - GAP;

/**
 * Play an already-authorized voice-note blob URL with a waveform and elapsed/total time.
 * Input: `url`, the object URL that `MediaPreview` created and still owns (this
 * component never creates, fetches over the network, or revokes a URL). Behavior:
 * the native `<audio controls>` stays the accessible control; the waveform is
 * `aria-hidden`, shows 64 bars (copper played, mineral remaining) and a click seeks
 * with the mouse (keyboard users seek with the native control). The bytes are read
 * from the local blob URL and decoded once with `AudioContext.decodeAudioData`; the
 * context is closed afterwards. If `AudioContext` is missing or decoding fails, only
 * the native player is shown. Side effects: one local blob read and one short-lived
 * AudioContext per URL. No transitions are used, so reduced motion needs no override.
 * Authority: none; it displays bytes the server already authorized.
 */
export function AudioWaveform({ url }: { url: string }) {
  const audio = useRef<HTMLAudioElement>(null);
  const [peaks, setPeaks] = useState<number[] | null>(null);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  /** Decode the blob once per URL; ignore a result that arrives after the URL changed or the owner unmounted. */
  useEffect(
    /** Read and decode the local blob, then publish normalized peaks. */
    function decodePeaks() {
      let cancelled = false;
      setPeaks(null);
      const Context =
        typeof window !== "undefined" ? window.AudioContext : undefined;
      if (!Context) return;
      void (
        /** Read the blob, decode it, and always close the AudioContext. */
        async function decode() {
          let context: AudioContext | null = null;
          try {
            const bytes = await (await fetch(url)).arrayBuffer();
            context = new Context();
            const buffer = await context.decodeAudioData(bytes);
            if (!cancelled)
              setPeaks(
                normalizePeaks(computePeaks(buffer.getChannelData(0), BUCKETS)),
              );
          } catch {
            if (!cancelled) setPeaks(null);
          } finally {
            void context?.close().catch(() => undefined);
          }
        }
      )();
      /** Stop a pending decode from updating state after this URL is gone. */
      return function cancelDecode() {
        cancelled = true;
      };
    },
    [url],
  );
  /** Seek proportionally to a mouse click on the waveform; ignored until the duration is known. */
  function seek(event: React.MouseEvent<HTMLDivElement>) {
    const element = audio.current;
    if (!element || !Number.isFinite(element.duration) || element.duration <= 0)
      return;
    const box = event.currentTarget.getBoundingClientRect();
    if (box.width <= 0) return;
    const ratio = Math.min(
      1,
      Math.max(0, (event.clientX - box.left) / box.width),
    );
    element.currentTime = ratio * element.duration;
    setTime(element.currentTime);
  }
  /** Copy the player's clock into state so the played bars and the text follow playback. */
  function syncClock() {
    const element = audio.current;
    if (!element) return;
    setTime(element.currentTime);
    setDuration(Number.isFinite(element.duration) ? element.duration : 0);
  }
  const played = duration > 0 ? time / duration : 0;
  return (
    <div className="audio-waveform">
      {peaks && (
        <div className="waveform-body">
          <div className="waveform-track" aria-hidden="true" onClick={seek}>
            <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="none">
              {peaks.map((peak, index) => {
                const barHeight = Math.max(2, peak * HEIGHT);
                return (
                  <rect
                    key={index}
                    x={index * (BAR + GAP)}
                    y={(HEIGHT - barHeight) / 2}
                    width={BAR}
                    height={barHeight}
                    rx={1}
                    className={
                      (index + 0.5) / BUCKETS <= played
                        ? "waveform-played"
                        : "waveform-remaining"
                    }
                  />
                );
              })}
            </svg>
          </div>
          <span className="waveform-time">
            {formatClock(time)} / {formatClock(duration)}
          </span>
        </div>
      )}
      <audio
        ref={audio}
        controls
        preload="metadata"
        src={url}
        aria-label="Voice note audio"
        onTimeUpdate={syncClock}
        onLoadedMetadata={syncClock}
        onDurationChange={syncClock}
        onSeeked={syncClock}
        onEnded={syncClock}
      />
    </div>
  );
}
