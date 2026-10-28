"use client";

import { useSyncExternalStore } from "react";

/** Coarse rendering-cost heuristic for the living-core point cloud's particle budget. */
export type DeviceTier = "desktop" | "mobile" | "low-power";

const NARROW_VIEWPORT_QUERY = "(max-width: 640px)";

interface NavigatorWithMemory extends Navigator {
  deviceMemory?: number;
}

function detectLowPower(): boolean {
  if (typeof navigator === "undefined") {
    return false;
  }
  const cores = navigator.hardwareConcurrency ?? 8;
  const memory = (navigator as NavigatorWithMemory).deviceMemory ?? 8;
  // Conservative thresholds: either signal alone being low is enough to drop
  // to the cheapest tier, since either one being low is a real bottleneck
  // for a particle-count-bound render.
  return cores <= 4 || memory <= 4;
}

// `hardwareConcurrency`/`deviceMemory` never change after load, so only the
// narrow-viewport media query needs a live subscription.
function subscribe(callback: () => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }
  const mediaQuery = window.matchMedia(NARROW_VIEWPORT_QUERY);
  mediaQuery.addEventListener("change", callback);
  return () => mediaQuery.removeEventListener("change", callback);
}

function getSnapshot(): DeviceTier {
  if (typeof window === "undefined") {
    return "mobile";
  }
  if (detectLowPower()) {
    return "low-power";
  }
  return window.matchMedia(NARROW_VIEWPORT_QUERY).matches ? "mobile" : "desktop";
}

function getServerSnapshot(): DeviceTier {
  // Safe default before hydration: the cheapest non-low-power tier, never "desktop".
  return "mobile";
}

/**
 * Resize-aware device-tier estimate, read via `useSyncExternalStore` so it never triggers a
 * cascading extra render.
 */
export function useDeviceTier(): DeviceTier {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
