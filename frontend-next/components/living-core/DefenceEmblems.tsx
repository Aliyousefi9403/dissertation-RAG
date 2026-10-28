"use client";

import type { ShieldState } from "@/lib/living-core/defenceShield";
import type { MonitorTrace } from "@/lib/types/monitor";

// Centrepieces over the living core, one per defence (Defended keeps DefenceShield).
// Purely presentational SVG; the only data shown are real counts from the last answer.

interface EmblemProps {
  state: ShieldState;
  variant: "stage" | "inline";
}

// ============================================================
// Repaired: a page whose suspect words are stitched back
// ============================================================

const LINES = [190, 160, 176, 140, 182, 120, 168];
const PATCHES: Array<[number, number, number]> = [
  [0, 52, 34],
  [2, 96, 30],
  [3, 20, 38],
  [4, 120, 28],
  [5, 40, 32],
  [6, 90, 36],
];

export function RepairLoom({
  state,
  variant,
  repaired,
}: EmblemProps & { repaired: number | null }) {
  const shown = state === "resolved" && repaired ? Math.min(repaired, PATCHES.length) : 0;
  const caption =
    state === "scanning"
      ? "Repair loom: checking every word"
      : state === "resolved" && repaired !== null
        ? repaired === 0
          ? "Repair loom: nothing needed repair"
          : `Repair loom: ${repaired} ${repaired === 1 ? "word" : "words"} restored`
        : state === "fault"
          ? "Repair loom: request failed"
          : "Repair loom ready";

  return (
    <div
      className={`defence-emblem defence-emblem--${variant} emblem-repair`}
      data-state={state}
      data-testid="emblem-repair"
    >
      <svg viewBox="-140 -150 280 300" aria-hidden="true" focusable="false">
        <rect x="-110" y="-120" width="220" height="240" rx="14" className="emblem-repair-page" />
        {LINES.map((width, row) => (
          <rect
            key={row}
            x="-90"
            y={-92 + row * 30}
            width={width}
            height="8"
            rx="4"
            className="emblem-repair-line"
          />
        ))}
        {PATCHES.map(([row, x, width], index) => (
          <rect
            key={index}
            x={-90 + x}
            y={-94 + row * 30}
            width={width}
            height="12"
            rx="3"
            className="emblem-repair-patch"
            data-fixed={index < shown}
            style={{ animationDelay: `${0.4 + index * 0.25}s` }}
          />
        ))}
        <rect x="-96" y="-104" width="3" height="208" rx="1.5" className="emblem-repair-caret" />
      </svg>
      <p className="defence-emblem-caption" role="status" aria-live="polite">
        {caption}
      </p>
    </div>
  );
}

// ============================================================
// Contextual: a language-model lens scanning the sentences
// ============================================================

const TICKS = Array.from({ length: 60 }, (_, i) => (i * 6 * Math.PI) / 180);
const EJECTED: Array<[number, number]> = [
  [118, -70],
  [-122, 52],
  [96, 98],
  [-104, -92],
  [130, 20],
];

export function ContextLensEmblem({
  state,
  variant,
  skipped,
}: EmblemProps & { skipped: number | null }) {
  const ejected = state === "resolved" && skipped ? Math.min(skipped, EJECTED.length) : 0;
  const caption =
    state === "scanning"
      ? "Context lens: reading each passage in context"
      : state === "resolved" && skipped !== null
        ? skipped === 0
          ? "Context lens: every passage fits"
          : `Context lens: ${skipped} ${skipped === 1 ? "passage" : "passages"} did not fit`
        : state === "fault"
          ? "Context lens: request failed"
          : "Context lens ready";

  return (
    <div
      className={`defence-emblem defence-emblem--${variant} emblem-lens`}
      data-state={state}
      data-testid="emblem-lens"
    >
      <svg viewBox="-140 -150 280 300" aria-hidden="true" focusable="false">
        <defs>
          <clipPath id="lens-clip">
            <circle r="88" />
          </clipPath>
        </defs>
        <g className="emblem-lens-ticks">
          {TICKS.map((a, i) => (
            <line
              key={i}
              x1={Math.cos(a) * 100}
              y1={Math.sin(a) * 100}
              x2={Math.cos(a) * (i % 5 === 0 ? 112 : 106)}
              y2={Math.sin(a) * (i % 5 === 0 ? 112 : 106)}
            />
          ))}
        </g>
        <circle r="96" className="emblem-lens-rim" />
        <g clipPath="url(#lens-clip)">
          {[-48, -24, 0, 24, 48].map((y, i) => (
            <rect
              key={y}
              x={-80 + (i % 2) * 10}
              y={y - 4}
              width={150 - (i % 3) * 20}
              height="8"
              rx="4"
              className="emblem-lens-line"
            />
          ))}
          <circle r="22" className="emblem-lens-focus" />
        </g>
        {EJECTED.slice(0, ejected).map(([x, y], i) => (
          <circle
            key={i}
            r="6"
            cx={x}
            cy={y}
            className="emblem-lens-ejected"
            style={{ animationDelay: `${0.5 + i * 0.25}s` }}
          />
        ))}
      </svg>
      <p className="defence-emblem-caption" role="status" aria-live="polite">
        {caption}
      </p>
    </div>
  );
}

// ============================================================
// Verified: a monitor gate with one node per rule
// ============================================================

type NodeState = "idle" | "pass" | "fixed" | "fail";

function ruleState(trace: MonitorTrace | null, spec: string): NodeState {
  if (!trace) return "idle";
  const seen = trace.rounds.some((r) => r.violations.some((v) => v.spec === spec));
  const open = trace.final_violations.some((v) => v.spec === spec);
  return open ? "fail" : seen ? "fixed" : "pass";
}

const NODES: Array<{ id: string; label: string; x: number; y: number }> = [
  { id: "phi1_lexical", label: "φ₁", x: -82, y: -62 },
  { id: "phi2_availability", label: "φ₂", x: 82, y: -62 },
  { id: "phi3_memory", label: "φ₃", x: 0, y: 92 },
];
const octagon = (radius: number) =>
  Array.from({ length: 8 }, (_, i) => {
    const a = Math.PI / 8 + (i * Math.PI) / 4;
    return `${(Math.cos(a) * radius).toFixed(1)},${(Math.sin(a) * radius).toFixed(1)}`;
  }).join(" ");
const OCTAGON = octagon(120);
const OCTAGON_INNER = octagon(98);

export function MonitorGate({
  state,
  variant,
  trace,
}: EmblemProps & { trace: MonitorTrace | null }) {
  const quarantined = trace
    ? trace.rounds.reduce((n, r) => n + (r.quarantined?.length ?? 0), 0)
    : 0;
  const skipped = trace?.rounds[0]?.skipped_quarantined ?? 0;
  const nodeState = (id: string): NodeState =>
    id === "phi3_memory" ? (trace ? "pass" : "idle") : ruleState(trace, id);
  const caption =
    state === "scanning"
      ? "Monitor: checking the answer"
      : state === "resolved" && trace
        ? {
            released: "Monitor: verified",
            released_refusal: "Monitor: evidence missing",
            restored: "Monitor: restored from MITRE",
            withheld: "Monitor: answer withheld",
          }[trace.outcome] +
          (quarantined ? ` · ${quarantined} quarantined` : "") +
          (skipped ? ` · ${skipped} skipped from memory` : "")
        : state === "fault"
          ? "Monitor: request failed"
          : "Monitor armed";

  return (
    <div
      className={`defence-emblem defence-emblem--${variant} emblem-gate`}
      data-state={state}
      data-outcome={trace?.outcome ?? "none"}
      data-testid="emblem-gate"
    >
      <svg viewBox="-140 -150 280 300" aria-hidden="true" focusable="false">
        <polygon points={OCTAGON} className="emblem-gate-frame" />
        <polygon points={OCTAGON_INNER} className="emblem-gate-frame emblem-gate-frame--inner" />
        {NODES.map((n) => (
          <line
            key={`l-${n.id}`}
            x1="0"
            y1="0"
            x2={n.x}
            y2={n.y}
            className="emblem-gate-link"
            data-node={nodeState(n.id)}
          />
        ))}
        <circle r="30" className="emblem-gate-core" />
        <text y="8" textAnchor="middle" className="emblem-gate-glyph">
          ⌘
        </text>
        {NODES.map((n) => (
          <g
            key={n.id}
            transform={`translate(${n.x} ${n.y})`}
            className="emblem-gate-node"
            data-node={nodeState(n.id)}
          >
            <circle r="20" />
            <text y="6" textAnchor="middle">
              {n.label}
            </text>
          </g>
        ))}
      </svg>
      <p className="defence-emblem-caption" role="status" aria-live="polite">
        {caption}
      </p>
    </div>
  );
}
