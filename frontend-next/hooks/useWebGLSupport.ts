"use client";

import { useSyncExternalStore } from "react";

export type WebGLSupportState = "checking" | "supported" | "unsupported";

function detectWebGLSupport(): boolean {
  try {
    const canvas = document.createElement("canvas");
    const gl =
      canvas.getContext("webgl2") ||
      canvas.getContext("webgl") ||
      canvas.getContext("experimental-webgl");

    if (gl && typeof (gl as WebGLRenderingContext).getExtension === "function") {
      const loseContext = (gl as WebGLRenderingContext).getExtension(
        "WEBGL_lose_context",
      );
      loseContext?.loseContext();
    }

    return Boolean(gl);
  } catch {
    return false;
  }
}

// Feature detection only ever needs to run once per page load — cached at
// module scope so `getSnapshot` stays referentially stable across renders
// (a `useSyncExternalStore` requirement) instead of re-probing every call.
let cachedSupport: boolean | null = null;

function getSnapshot(): WebGLSupportState {
  if (cachedSupport === null) {
    cachedSupport = detectWebGLSupport();
  }
  return cachedSupport ? "supported" : "unsupported";
}

function getServerSnapshot(): WebGLSupportState {
  return "checking";
}

function subscribe() {
  // The result of a one-time synchronous feature probe never changes after
  // first read, so there is nothing to subscribe to.
  return () => {};
}

/**
 * Pre-mount WebGL feature detection, read synchronously via
 * `useSyncExternalStore` (never a `setState` call inside a `useEffect`) so
 * callers can gate `<Canvas>` mounting before any three.js /
 * `@react-three/*` module is evaluated.
 */
export function useWebGLSupport(): WebGLSupportState {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
