/**
 * Shared exponential-decay smoothing helper used by every living-core r3f component that eases
 * a uniform/scale toward a phase-derived target instead of snapping it.
 */
export function damp(current: number, target: number, lambda: number, dt: number): number {
  return current + (target - current) * (1 - Math.exp(-lambda * dt));
}
