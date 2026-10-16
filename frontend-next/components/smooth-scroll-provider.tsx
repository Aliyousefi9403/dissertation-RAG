"use client";

import "lenis/dist/lenis.css";

import { ReactLenis } from "lenis/react";

export function SmoothScrollProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ReactLenis
      root
      // `root: true` hijacks wheel/touch input for the document root
      // (window/documentElement), but this app never scrolls the document
      // itself (`body { overflow: hidden }` by design) -- every scrollable
      // region is a nested internal container (`.conversation`,
      // `.kb-content`, ...). Without `allowNestedScroll`, Lenis's `onWheel`
      // unconditionally calls `preventDefault()` on every wheel event
      // (node_modules/lenis/dist/lenis.mjs) before the browser's native
      // scroll can reach those containers, silently breaking scrolling
      // everywhere. `allowNestedScroll: true` makes Lenis auto-detect any
      // genuinely-overflowing `overflow-y/x: auto|scroll` ancestor in the
      // wheel event's path (`hasNestedScroll`) and step aside for it --
      // no per-container opt-out attribute needed, works for every current
      // and future internal scroll container automatically.
      options={{ lerp: 0.1, duration: 1.2, smoothWheel: true, allowNestedScroll: true }}
    >
      {children}
    </ReactLenis>
  );
}
