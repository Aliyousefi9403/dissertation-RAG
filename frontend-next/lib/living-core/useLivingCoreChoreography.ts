"use client";

import { useEffect, useState } from "react";

import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";

/**
 * Presentation-only rendering beats layered on top of `LivingCorePhase`.
 * None of these are new `ChatState`/phase values — they never gate the real
 * answer/status text (that lives entirely in `LivingCoreStage`'s DOM
 * caption and `AnswerPanel`, and reads `phase` directly). This hook is the
 * ONLY place that owns them.
 *
 * - "idle": the resting beat for dormant/idle/unresolved/fault — no
 *   sequencing, just a steady state for those components to render their
 *   own phase-driven ambient motion (breathing, drift, fault flicker).
 * - "retrieving" / "generating": a looping two-stage sub-sequence that only
 *   plays while `phase === "submitting"`. There is no backend-level
 *   distinction between "retrieving" and "generating" — `/chat` is one
 *   non-streaming POST — so this is purely an ambient rendering cadence
 *   (anonymous energy pulsing toward the core, then the core
 *   compressing/synthesizing) representing "a request is in flight," not a
 *   claim about literal backend stages. It loops for as long as
 *   "submitting" lasts, however long the real request takes.
 * - "arriving" / "linking" / "resolved": the existing converged-phase
 *   sequence (source nodes easing into formation, then evidence energy
 *   flowing into the core, then settling) — unchanged from the retired
 *   `useShieldChoreography.ts`.
 *
 * During "retrieving"/"generating", consumers (`NeuralPointCloud`,
 * `NeuralConnections`, `RetrievalScan`) must render only anonymous
 * energy/pulses — never numbered source badges, since real source numbers
 * do not exist until the response actually arrives.
 */
export type LivingCoreChoreographyBeat =
  | "idle"
  | "retrieving"
  | "generating"
  | "arriving"
  | "linking"
  | "resolved";

export interface LivingCoreChoreographyState {
  beat: LivingCoreChoreographyBeat;
  /** `performance.now()` timestamp (ms) the current beat started. Exposed
   * so per-frame r3f consumers can derive their own animation progress
   * inside `useFrame` without this hook forcing a React re-render every
   * animation frame — the same imperative-ref pattern the rest of the
   * living-core scene uses. */
  beatStartedAt: number;
}

export const DEFAULT_RETRIEVING_MS = 1100;
export const DEFAULT_GENERATING_MS = 1500;
export const DEFAULT_ARRIVING_MS = 450;
export const DEFAULT_LINKING_MS = 550;

interface UseLivingCoreChoreographyOptions {
  phase: LivingCorePhase;
  /** Duration, in ms, of each "submitting" sub-beat loop iteration. */
  retrievingMs?: number;
  generatingMs?: number;
  /** Duration, in ms, of the "arriving" beat (source nodes easing into
   * their formation around the core). */
  arrivingMs?: number;
  /** Duration, in ms, of the "linking" beat (evidence energy travelling
   * from each source node into the core). */
  linkingMs?: number;
}

function now(): number {
  return typeof performance !== "undefined" ? performance.now() : 0;
}

function restingBeatFor(phase: LivingCorePhase): LivingCoreChoreographyBeat {
  if (phase === "submitting") {
    return "retrieving";
  }
  if (phase === "converged") {
    return "resolved";
  }
  return "idle";
}

/**
 * Presentation-only choreography for (a) the entire duration of a
 * "submitting" request and (b) the moment a request resolves into
 * "converged". This hook never reads or writes the app's chat state
 * machine, and it is not a gate on anything: it only watches the
 * already-derived `phase` value from `livingCoreState.ts` (whose contract
 * is untouched) and, purely for `LivingCoreScene`'s internal r3f children,
 * sequences short, capped-duration rendering beats.
 *
 * The real answer and real sources are already fully available the instant
 * `phase` becomes "converged"; `LivingCoreStage`'s DOM answer panel and
 * `aria-live` status caption read `phase` directly and never consume this
 * hook, so they update immediately and are never gated behind this
 * animation.
 *
 * The phase-change detection uses React's documented "adjusting state when
 * a prop changes" render-phase pattern (comparing against `renderedPhase`
 * during render, not inside an effect) rather than calling `setState`
 * synchronously from an effect body — every subsequent beat advance is then
 * driven by its own small effect, whose `setState` call only ever happens
 * inside an async `setTimeout` callback.
 */
export function useLivingCoreChoreography({
  phase,
  retrievingMs = DEFAULT_RETRIEVING_MS,
  generatingMs = DEFAULT_GENERATING_MS,
  arrivingMs = DEFAULT_ARRIVING_MS,
  linkingMs = DEFAULT_LINKING_MS,
}: UseLivingCoreChoreographyOptions): LivingCoreChoreographyState {
  const [renderedPhase, setRenderedPhase] = useState(phase);
  const [state, setState] = useState<LivingCoreChoreographyState>(() => ({
    beat: restingBeatFor(phase) === "resolved" ? "resolved" : "idle",
    beatStartedAt: now(),
  }));

  if (phase !== renderedPhase) {
    setRenderedPhase(phase);
    const nextBeat: LivingCoreChoreographyBeat =
      phase === "converged" ? "arriving" : phase === "submitting" ? "retrieving" : "idle";
    setState({ beat: nextBeat, beatStartedAt: now() });
  }

  // "submitting" loop: retrieving -> generating -> retrieving -> ...,
  // for as long as the phase stays "submitting" — the real request may
  // take any amount of time, so this is a repeating ambient cadence, not a
  // one-shot animation with a real endpoint.
  useEffect(() => {
    if (phase !== "submitting") {
      return;
    }
    if (state.beat !== "retrieving" && state.beat !== "generating") {
      return;
    }
    const duration = state.beat === "retrieving" ? retrievingMs : generatingMs;
    const nextBeat: LivingCoreChoreographyBeat =
      state.beat === "retrieving" ? "generating" : "retrieving";
    const timer = window.setTimeout(() => {
      setState({ beat: nextBeat, beatStartedAt: now() });
    }, duration);
    return () => window.clearTimeout(timer);
  }, [phase, state.beat, state.beatStartedAt, retrievingMs, generatingMs]);

  // Advances "arriving" -> "linking" after `arrivingMs`. Depends on
  // `state.beatStartedAt` (not just `state.beat`) so a later fresh
  // "arriving" beat always reschedules its own timer.
  useEffect(() => {
    if (state.beat !== "arriving") {
      return;
    }
    const timer = window.setTimeout(() => {
      setState({ beat: "linking", beatStartedAt: now() });
    }, arrivingMs);
    return () => window.clearTimeout(timer);
  }, [state.beat, state.beatStartedAt, arrivingMs]);

  // Advances "linking" -> "resolved" after `linkingMs`.
  useEffect(() => {
    if (state.beat !== "linking") {
      return;
    }
    const timer = window.setTimeout(() => {
      setState({ beat: "resolved", beatStartedAt: now() });
    }, linkingMs);
    return () => window.clearTimeout(timer);
  }, [state.beat, state.beatStartedAt, linkingMs]);

  return state;
}
