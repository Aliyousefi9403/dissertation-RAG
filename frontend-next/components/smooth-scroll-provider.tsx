"use client";

import "lenis/dist/lenis.css";

import { ReactLenis } from "lenis/react";

export function SmoothScrollProvider({ children }: { children: React.ReactNode }) {
  return (
    <ReactLenis
      root
      // `root: true` hijacks wheel/touch input for the document root.
      options={{ lerp: 0.1, duration: 1.2, smoothWheel: true, allowNestedScroll: true }}
    >
      {children}
    </ReactLenis>
  );
}
