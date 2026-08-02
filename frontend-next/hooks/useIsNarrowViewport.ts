"use client";

import { useSyncExternalStore } from "react";

const NARROW_VIEWPORT_QUERY = "(max-width: 640px)";

function subscribe(callback: () => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }
  const mediaQuery = window.matchMedia(NARROW_VIEWPORT_QUERY);
  mediaQuery.addEventListener("change", callback);
  return () => mediaQuery.removeEventListener("change", callback);
}

function getSnapshot(): boolean {
  return window.matchMedia(NARROW_VIEWPORT_QUERY).matches;
}

function getServerSnapshot(): boolean {
  // Safe default: assume a normal (non-narrow) viewport until the client
  // measures the real one. This only tunes rendering cost (device-pixel
  // ratio cap for the shield-core scene), never whether it renders, so a
  // brief over-estimate on first paint is an acceptable trade-off.
  return false;
}

/**
 * Resize-aware narrow-viewport check, read via `useSyncExternalStore`
 * (never `setState` inside a `useEffect`) so it never triggers a
 * cascading extra render. Used purely to tune the shield-core 3D scene's
 * rendering cost (device-pixel-ratio cap) — it never gates *whether* the
 * scene renders, that stays driven entirely by WebGL support and the
 * reduced-motion preference (see `ShieldCoreStage`).
 */
export function useIsNarrowViewport(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
