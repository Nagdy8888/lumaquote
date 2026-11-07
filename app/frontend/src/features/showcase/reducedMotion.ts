import { useEffect, useState } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

/**
 * Follow the system reduced-motion preference without importing Three.js, so a page can decide
 * whether to request a lazy 3D chunk at all.
 * Output: true while the user asks for reduced motion; it updates live when the setting changes.
 * Side effects: one media-query listener, removed on unmount. Invariant: callers that receive true
 * render their static content and create no canvas (tests/integration/test_scene_review.py).
 */
export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => matchMedia(QUERY).matches);
  useEffect(
    /** Subscribe to preference changes and return the unsubscribe function. */
    function observeMotionPreference() {
      const query = matchMedia(QUERY);
      /** Mirror a live change of the system setting. */
      function motionChanged() {
        setReduced(query.matches);
      }
      query.addEventListener("change", motionChanged);
      /** Remove the media-query listener on unmount. */
      return function cleanup() {
        query.removeEventListener("change", motionChanged);
      };
    },
    [],
  );
  return reduced;
}
