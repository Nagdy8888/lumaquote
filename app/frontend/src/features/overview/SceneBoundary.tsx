import { Component, type ErrorInfo, type ReactNode } from "react";
import { LampCeiling } from "lucide-react";

/** Provide a lightweight, meaningful static scene when WebGL, motion, or the lazy chunk is unavailable. */
export function LightingFallback() {
  return (
    <div className="lighting-fallback">
      <LampCeiling strokeWidth={1} />
      <span>Light, thoughtfully specified.</span>
      <small>Illustrative product scene</small>
    </div>
  );
}

/** Contain optional rendering failures so the sales workflow never depends on Three.js or WebGL. */
export class SceneBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  /** Replace a failed optional scene with static content rather than propagating to the application shell. */
  static getDerivedStateFromError() {
    return { failed: true };
  }
  /** Intentionally avoid exporting rendering errors or local environment details to third-party telemetry. */
  componentDidCatch(_error: Error, _info: ErrorInfo) {
    /* The static scene remains usable. */
  }
  /** Render the lazy child, or the caller's fallback (default: the lighting fallback) after a failure. */
  render() {
    if (!this.state.failed) return this.props.children;
    return this.props.fallback ?? <LightingFallback />;
  }
}
