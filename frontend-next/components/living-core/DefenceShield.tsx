"use client";

import type { ShieldState } from "@/lib/living-core/defenceShield";

interface DefenceShieldProps {
  state: ShieldState;
  /** Real count from `skippedPassageCount` (null = not known yet). */
  skipped: number | null;
  /** "stage" = centred over the fullscreen 3D core; "inline" = beside the
   * static fallback card (no WebGL / reduced motion). */
  variant?: "stage" | "inline";
  /** Repaired mode: real count of words the repair policy replaced. */
  repaired?: number | null;
  /** Contextual mode: the filter's reference q is a language model. */
  contextual?: boolean;
}

// Heater-shield outline centred on (0, 0) in a 240 x 280 viewBox.
const SHIELD =
  "M0,-122 C38,-104 74,-98 100,-94 L100,-12 C100,58 56,98 0,126 C-56,98 -100,58 -100,-12 L-100,-94 C-74,-98 -38,-104 0,-122 Z";
const INNER =
  "M0,-100 C31,-85 61,-80 82,-77 L82,-10 C82,47 46,80 0,103 C-46,80 -82,47 -82,-10 L-82,-77 C-61,-80 -31,-85 0,-100 Z";
// Pointy-top honeycomb: hex radius 13.86, tile 24 x 41.57.
const HEX = (cx: number, cy: number) =>
  `M${cx},${cy - 13.86} L${cx + 12},${cy - 6.93} L${cx + 12},${cy + 6.93} L${cx},${cy + 13.86} L${cx - 12},${cy + 6.93} L${cx - 12},${cy - 6.93} Z`;
const HONEYCOMB = [HEX(0, 0), HEX(24, 0), HEX(12, 20.78), HEX(0, 41.57), HEX(24, 41.57)].join(" ");
// Where "blocked" passages strike the shield (unit points on the rim).
// Lower rim first: the upper half usually sits behind the answer card.
const IMPACTS: Array<[number, number]> = [
  [-70, 76],
  [70, 76],
  [0, 120],
  [-96, 30],
  [96, 30],
  [-40, 104],
  [40, 104],
  [-100, -40],
  [100, -40],
  [0, -116],
];
const IMPACT_DELAY = 0.6;
const IMPACT_STEP = 0.32;

/**
 * The Defended-mode shield. Purely presentational (aria-hidden SVG); the only
 * data it shows is the real number of candidate passages the entropy filter
 * skipped for the last answer, in the caption, which is announced politely.
 * Every animation is CSS and is disabled under prefers-reduced-motion.
 */
export function DefenceShield({
  state,
  skipped,
  variant = "stage",
  repaired,
  contextual = false,
}: DefenceShieldProps) {
  const impacts = state === "resolved" && skipped ? Math.min(skipped, IMPACTS.length) : 0;
  const repairMode = repaired !== undefined;
  const repairNote =
    repairMode && state === "resolved" && repaired !== null
      ? ` · ${repaired} ${repaired === 1 ? "word" : "words"} repaired`
      : "";
  const caption =
    state === "scanning"
      ? "Entropy shield scanning candidates…"
      : state === "resolved" && skipped !== null
        ? (skipped === 0
            ? "Entropy shield: no passages blocked"
            : `Entropy shield: ${skipped} suspicious ${skipped === 1 ? "passage" : "passages"} blocked`) +
          repairNote
        : state === "fault"
          ? "Entropy shield: request failed"
          : repairMode
            ? "Entropy shield armed — repair, then re-check"
            : contextual
              ? "Entropy shield armed — language-model reference"
              : "Entropy shield armed — relative-entropy filter on";

  return (
    <div
      className={`defence-shield defence-shield--${variant}`}
      data-state={state}
      data-impacts={impacts > 0}
      data-mode={repairMode ? "repair" : contextual ? "contextual" : "filter"}
      data-testid="defence-shield"
    >
      <svg
        className="defence-shield-svg"
        viewBox="-140 -150 280 300"
        aria-hidden="true"
        focusable="false"
      >
        <defs>
          <linearGradient id="defence-face" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#7fd99a" stopOpacity="0.30" />
            <stop offset="55%" stopColor="#38bdf8" stopOpacity="0.10" />
            <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="defence-sweep" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0" />
            <stop offset="50%" stopColor="#c8f7d6" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
          <pattern
            id="defence-cells"
            width="24"
            height="41.57"
            patternUnits="userSpaceOnUse"
            x="-12"
            y="-14"
          >
            <path d={HONEYCOMB} fill="none" stroke="#7fd99a" strokeWidth="0.8" />
          </pattern>
          <clipPath id="defence-clip">
            <path d={SHIELD} />
          </clipPath>
          <filter id="defence-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="7" />
          </filter>
        </defs>

        <g className="defence-shield-ring defence-shield-ring--outer">
          <circle r="132" fill="none" stroke="#38bdf8" strokeWidth="1" strokeDasharray="2 9" />
        </g>
        <g className="defence-shield-ring defence-shield-ring--inner">
          <circle
            r="118"
            fill="none"
            stroke="#7fd99a"
            strokeWidth="1.4"
            strokeDasharray="38 14 4 14"
          />
        </g>

        <path d={SHIELD} className="defence-shield-halo" filter="url(#defence-glow)" />

        <g clipPath="url(#defence-clip)">
          <path d={SHIELD} fill="url(#defence-face)" />
          <rect
            className="defence-shield-cells"
            x="-110"
            y="-130"
            width="220"
            height="260"
            fill="url(#defence-cells)"
          />
          <rect
            className="defence-shield-sweep"
            x="-110"
            y="-130"
            width="220"
            height="60"
            fill="url(#defence-sweep)"
          />
        </g>

        <path d={SHIELD} className="defence-shield-edge" pathLength={1} />
        <path d={INNER} className="defence-shield-edge defence-shield-edge--inner" pathLength={1} />

        <text className="defence-shield-glyph" x="0" y="8" textAnchor="middle">
          D(p‖q)
        </text>

        {Array.from({ length: impacts }, (_, index) => {
          const [x, y] = IMPACTS[index];
          return (
            <g
              key={`${index}-${skipped}`}
              className="defence-shield-impact"
              style={{ transform: `translate(${x}px, ${y}px)` }}
            >
              <circle
                r="7"
                className="defence-shield-impact-core"
                style={{ animationDelay: `${IMPACT_DELAY + IMPACT_STEP * index}s` }}
              />
              <circle
                r="7"
                className="defence-shield-impact-ring"
                style={{ animationDelay: `${IMPACT_DELAY + IMPACT_STEP * index}s` }}
              />
            </g>
          );
        })}
      </svg>
      <p className="defence-shield-caption" role="status" aria-live="polite">
        {caption}
      </p>
      {impacts > 0 && (
        <div className="defence-shield-tokens" aria-hidden="true">
          {Array.from({ length: impacts }, (_, index) => (
            <span
              key={`${index}-${skipped}`}
              className="defence-shield-token"
              style={{ animationDelay: `${IMPACT_DELAY + IMPACT_STEP * index}s` }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
