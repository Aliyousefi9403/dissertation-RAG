"use client";

import { useSyncExternalStore } from "react";

/**
 * A tiny module-level pub/sub broadcasting the living core's current
 * rendering-intensity energy (`[0, 1]`) — the same value `LivingCoreStage`
 * already derives from real `ChatState`/`HealthStatus` via
 * `livingCoreState.ts` — so the page-root `DotFieldBackdrop` can give a
 * subtle, honest "reaction near the core" without `app/layout.tsx` needing
 * any knowledge of `ChatState` itself, and without threading props through
 * `app/page.tsx` (out of scope for this pass — see the living-core
 * hand-off notes).
 *
 * This does not compute anything new: it mirrors a value already derived
 * exclusively from `getLivingCorePhase`, so it does not introduce a second,
 * hidden interpretation of "security posture" — the cross-cutting rule in
 * `docs/frontend/living-core-states.md` still holds. `DotFieldBackdrop`
 * only ever reads this to bias brightness near a fixed on-screen anchor; it
 * never renders any text/number derived from it.
 */
let currentEnergy = 0;
const listeners = new Set<() => void>();

export function setLivingCoreActivityEnergy(energy: number): void {
  const clamped = Math.max(0, Math.min(1, energy));
  if (clamped === currentEnergy) {
    return;
  }
  currentEnergy = clamped;
  listeners.forEach((listener) => listener());
}

function subscribe(callback: () => void): () => void {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function getSnapshot(): number {
  return currentEnergy;
}

function getServerSnapshot(): number {
  return 0;
}

/** Read-only hook for consumers (`DotFieldBackdrop`) of the broadcast
 * energy value. */
export function useLivingCoreActivityEnergy(): number {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
