"use client";

import { useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";

import { useIsNarrowViewport } from "@/hooks/useIsNarrowViewport";
import { useLivingCoreActivityEnergy } from "@/lib/living-core/livingCoreActivityStore";

/** A deliberate SECOND canvas: a page-root ambient dot field. */
const DOT_SPACING_DESKTOP_PX = 64;
const DOT_SPACING_MOBILE_PX = 96;
const CORE_ANCHOR_RATIO = { x: 0.5, y: 0.4 };
const CORE_REACTION_RADIUS_PX = 260;
const MAX_DPR_DESKTOP = 2;
const MAX_DPR_MOBILE = 1.5;

interface Dot {
  x: number;
  y: number;
  seed: number;
}

// Deterministic hash instead of `Math.random()`, purely so the field looks
// identical across re-mounts/resizes at a given size rather than
// reshuffling — no functional requirement, just visual stability.
function hash(a: number, b: number): number {
  const value = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453;
  return value - Math.floor(value);
}

function buildDots(width: number, height: number, spacing: number): Dot[] {
  const dots: Dot[] = [];
  const cols = Math.ceil(width / spacing);
  const rows = Math.ceil(height / spacing);
  for (let row = 0; row <= rows; row += 1) {
    for (let col = 0; col <= cols; col += 1) {
      const jitterX = hash(row, col) - 0.5;
      const jitterY = hash(col, row) - 0.5;
      dots.push({
        x: col * spacing + jitterX * spacing * 0.5,
        y: row * spacing + jitterY * spacing * 0.5,
        seed: hash(row * 3.1, col * 7.7),
      });
    }
  }
  return dots;
}

export function DotFieldBackdrop() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dotsRef = useRef<Dot[]>([]);
  const rafRef = useRef<number | null>(null);
  const energyRef = useRef(0);
  const isVisibleRef = useRef(true);

  const reducedMotion = useReducedMotion();
  const isNarrowViewport = useIsNarrowViewport();
  const energy = useLivingCoreActivityEnergy();

  useEffect(() => {
    energyRef.current = energy;
  }, [energy]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) {
      return;
    }

    const spacing = isNarrowViewport ? DOT_SPACING_MOBILE_PX : DOT_SPACING_DESKTOP_PX;
    const dpr = Math.min(
      window.devicePixelRatio || 1,
      isNarrowViewport ? MAX_DPR_MOBILE : MAX_DPR_DESKTOP,
    );

    function resize() {
      const width = window.innerWidth;
      const height = window.innerHeight;
      canvas!.width = width * dpr;
      canvas!.height = height * dpr;
      canvas!.style.width = `${width}px`;
      canvas!.style.height = `${height}px`;
      context!.setTransform(dpr, 0, 0, dpr, 0, 0);
      dotsRef.current = buildDots(width, height, spacing);
    }

    function drawFrame(timeMs: number) {
      const width = window.innerWidth;
      const height = window.innerHeight;
      context!.clearRect(0, 0, width, height);

      const anchorX = width * CORE_ANCHOR_RATIO.x;
      const anchorY = height * CORE_ANCHOR_RATIO.y;
      const elapsed = timeMs / 1000;
      const currentEnergy = energyRef.current;
      const animate = reducedMotion === false;

      dotsRef.current.forEach((dot) => {
        const drift = animate ? Math.sin(elapsed * 0.12 + dot.seed * 10) * 1.2 : 0;
        const dx = dot.x - anchorX;
        const dy = dot.y - anchorY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const proximity = Math.max(0, 1 - distance / CORE_REACTION_RADIUS_PX);
        const reaction = proximity * currentEnergy;
        const alpha = 0.045 + reaction * 0.2 + dot.seed * 0.015;
        const radius = 0.9 + reaction * 1;

        context!.beginPath();
        context!.fillStyle =
          reaction > 0.12
            ? `rgba(125, 211, 252, ${alpha.toFixed(3)})`
            : `rgba(148, 163, 184, ${alpha.toFixed(3)})`;
        context!.arc(dot.x, dot.y + drift, radius, 0, Math.PI * 2);
        context!.fill();
      });
    }

    function loop(timeMs: number) {
      if (isVisibleRef.current) {
        drawFrame(timeMs);
      }
      rafRef.current = window.requestAnimationFrame(loop);
    }

    function handleVisibilityChange() {
      isVisibleRef.current = document.visibilityState === "visible";
    }

    resize();
    drawFrame(0);
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // `prefers-reduced-motion`: draw exactly one static frame and never start the animation
    // loop at all.
    if (reducedMotion !== false) {
      return () => {
        window.removeEventListener("resize", resize);
        document.removeEventListener("visibilitychange", handleVisibilityChange);
      };
    }

    rafRef.current = window.requestAnimationFrame(loop);

    return () => {
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (rafRef.current !== null) {
        window.cancelAnimationFrame(rafRef.current);
      }
    };
  }, [reducedMotion, isNarrowViewport]);

  return <canvas ref={canvasRef} className="dot-field-canvas" aria-hidden="true" />;
}
