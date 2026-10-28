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
  // Safe default: assume a normal viewport until the client measures the real one.
  return false;
}

/**
 * Resize-aware narrow-viewport check, read via `useSyncExternalStore` so it never triggers a
 * cascading extra render.
 */
export function useIsNarrowViewport(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
