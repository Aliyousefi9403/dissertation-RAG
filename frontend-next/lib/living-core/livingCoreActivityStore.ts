"use client";

import { useSyncExternalStore } from "react";

/** Tiny pub/sub for the living core's current energy level. */
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
