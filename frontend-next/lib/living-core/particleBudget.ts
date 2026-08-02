import type { DeviceTier } from "@/hooks/useDeviceTier";

/**
 * Particle count for `IntelligentParticleField`'s GPU-simulated point
 * cloud, keyed by the `useDeviceTier` rendering-cost heuristic. Every tier
 * stays within the 15,000-30,000 particle range: the field is a single
 * `THREE.Points` draw call with all motion computed per-vertex in the
 * shader (no CPU-side simulation, no extra render-target passes), so the
 * cost that scales with device tier is fill-rate/vertex-shader work only —
 * comfortably within budget at these counts on integrated GPUs, unlike a
 * multi-pass GPGPU approach would be.
 */
export const PARTICLE_COUNT: Record<DeviceTier, number> = {
  desktop: 28000,
  mobile: 18000,
  "low-power": 15000,
};

/** Number of concentric depth layers the point cloud's REST distribution is
 * built across (core / mid / outer) — see `particleFieldLayout.ts`. Purely
 * a static initial-layout concern; the per-frame curl-noise/breathing/
 * attraction motion in the shader has no notion of discrete layers. */
export const LAYER_COUNT = 3;

/** Fraction of the total particle budget assigned to each layer, core
 * first. Must sum to 1; the last layer absorbs any rounding remainder so
 * `positions.length` always matches `count * 3` exactly. */
export const LAYER_RATIOS: readonly number[] = [0.16, 0.34, 0.5];

/** Base radius (world units) of each layer's shell, before per-particle
 * jitter — also the rest radius the shader's gentle center-attraction pulls
 * each particle back toward, so the field keeps reading as one coherent
 * layered body instead of dispersing under curl-noise turbulence. */
export const LAYER_RADII: readonly number[] = [0.42, 0.8, 1.18];
