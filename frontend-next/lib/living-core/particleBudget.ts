import type { DeviceTier } from "@/hooks/useDeviceTier";

/** Particle count for `IntelligentParticleField`'s GPU-simulated point cloud. */
export const PARTICLE_COUNT: Record<DeviceTier, number> = {
  desktop: 84000,
  mobile: 54000,
  "low-power": 45000,
};

/** Number of concentric depth layers the point cloud's REST distribution is built across. */
export const LAYER_COUNT = 3;

/** Fraction of the total particle budget assigned to each layer, core
 * first. Must sum to 1; the last layer absorbs any rounding remainder so
 * `positions.length` always matches `count * 3` exactly. */
export const LAYER_RATIOS: readonly number[] = [0.16, 0.34, 0.5];

/** Base radius of each layer's shell, before per-particle jitter. */
export const LAYER_RADII: readonly number[] = [0.42, 0.8, 1.18];
