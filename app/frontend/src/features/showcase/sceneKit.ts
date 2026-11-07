import { useEffect, useRef, useState } from "react";
import { CanvasTexture, SRGBColorSpace } from "three";

/** Light temperatures shown in the illustrative scenes; values are display colours, not photometric data. */
export const LIGHT_COLOURS = {
  warm: "#ffc37a",
  neutral: "#ffe9cc",
  cool: "#cfe6ff",
} as const;

export type LightTemperature = keyof typeof LIGHT_COLOURS;

/**
 * Decide how an optional decorative canvas renders.
 * Output: `reduced` follows the system motion preference live; callers must then render their
 * static fallback and no canvas (tests/integration/test_scene_review.py). `frameloop` is "never"
 * while the canvas is off screen or the tab is hidden, else "always". Side effects: one
 * media-query listener, one IntersectionObserver and one visibilitychange listener, all released
 * on unmount. Invariant: nothing renders frames when nobody can see the canvas.
 */
export function useScenePlayback<T extends Element>() {
  const ref = useRef<T>(null);
  const [reduced, setReduced] = useState(
    () => matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  const [onScreen, setOnScreen] = useState(true);
  const [pageVisible, setPageVisible] = useState(
    () => document.visibilityState !== "hidden",
  );
  useEffect(
    /** Track motion preference, viewport intersection and tab visibility; return their cleanup. */
    function observePlayback() {
      const query = matchMedia("(prefers-reduced-motion: reduce)");
      /** Mirror a live change of the system reduced-motion setting. */
      function motionChanged() {
        setReduced(query.matches);
      }
      /** Pause rendering while the browser tab is hidden. */
      function visibilityChanged() {
        setPageVisible(document.visibilityState !== "hidden");
      }
      query.addEventListener("change", motionChanged);
      document.addEventListener("visibilitychange", visibilityChanged);
      const observer =
        typeof IntersectionObserver === "undefined" || !ref.current
          ? null
          : new IntersectionObserver(
              /** Record whether any part of the canvas wrapper is inside the viewport. */
              function intersected(entries) {
                setOnScreen(entries.some((entry) => entry.isIntersecting));
              },
            );
      if (observer && ref.current) observer.observe(ref.current);
      /** Release every listener and the observer when the scene unmounts. */
      return function cleanup() {
        query.removeEventListener("change", motionChanged);
        document.removeEventListener("visibilitychange", visibilityChanged);
        observer?.disconnect();
      };
    },
    [],
  );
  const frameloop: "always" | "never" =
    !onScreen || !pageVisible ? "never" : "always";
  return { ref, reduced, frameloop };
}

let glow: CanvasTexture | null = null;

/**
 * Return one shared radial-gradient texture used for additive light halos.
 * Side effect: creates a 128px canvas once per page load and caches the texture; callers must not
 * dispose it. Errors: throws only if the browser cannot create a 2D canvas context, which the
 * surrounding SceneBoundary turns into the static fallback.
 */
export function glowTexture() {
  if (glow) return glow;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 128;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("2D canvas unavailable for light halo");
  const gradient = context.createRadialGradient(64, 64, 0, 64, 64, 64);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.18, "rgba(255,255,255,0.55)");
  gradient.addColorStop(0.5, "rgba(255,255,255,0.12)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, 128, 128);
  glow = new CanvasTexture(canvas);
  glow.colorSpace = SRGBColorSpace;
  return glow;
}

/**
 * Ease a 0..1 ignition value for lamp `index` at elapsed seconds `time`.
 * Inputs: `delay` seconds before the first lamp, `stagger` seconds between lamps. Output is 0 before
 * the lamp's turn, a short flicker, then 1. Pure function.
 */
export function ignition(time: number, index: number, delay = 0.4, stagger = 0.35) {
  const local = time - delay - index * stagger;
  if (local <= 0) return 0;
  if (local >= 0.6) return 1;
  const flicker = local < 0.25 ? (Math.sin(local * 90) > 0 ? 0.7 : 0.15) : 1;
  return Math.min(1, (local / 0.6) * 1.4) * flicker;
}
