"use client";

import { useEffect, useState } from "react";

import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";

/** Presentation-only rendering beats layered on top of `LivingCorePhase`. */
export type LivingCoreChoreographyBeat =
  | "idle"
  | "retrieving"
  | "generating"
  | "arriving"
  | "linking"
  | "resolved";

export interface LivingCoreChoreographyState {
  beat: LivingCoreChoreographyBeat;
  /** `performance.now` timestamp the current beat started. */
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
 * Presentation-only choreography for the entire duration of a "submitting" request and the
 * moment a request resolves into "converged".
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

  // "submitting" loop: retrieving -> generating -> retrieving ->.
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
