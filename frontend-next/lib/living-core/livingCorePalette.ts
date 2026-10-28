import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";

/** Shared color tokens for every living-core visual phase, used by the 3D scene. */
export const LIVING_CORE_PHASE_COLOR: Record<LivingCorePhase, string> = {
  dormant: "#3d4650",
  idle: "#38bdf8",
  submitting: "#22d3ee",
  converged: "#8be9fd",
  unresolved: "#3b6675",
  fault: "#b3554f",
};

/** Metallic edge tokens for `ShieldOutline`. */
export const LIVING_CORE_SHIELD_COLOR: Record<LivingCorePhase, string> = {
  dormant: "#454d57",
  idle: "#9fb4c4",
  submitting: "#bfe3f2",
  converged: "#cfeaf5",
  unresolved: "#6b7f8c",
  fault: "#9c6b67",
};
