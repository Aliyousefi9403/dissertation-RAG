import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";

/**
 * Shared color tokens for every living-core visual phase, used by the 3D
 * scene (`ShieldOutline`, `NeuralPointCloud`, `NeuralConnections`,
 * `SourceLinkPaths`, `RetrievalScan`), the dot-field backdrop, and the
 * DOM/CSS static fallback (`app/globals.css` `.living-core-glyph[data-phase]`
 * rules), so every presentation stays in visual agreement.
 *
 * Restrained graphite/silver/cool-white/cyan spectrum only — no purple,
 * pink, gold, or rainbow hues anywhere. Every phase except "fault" is told
 * apart by brightness/saturation and motion pattern, never by hue; "fault"
 * is the one phase allowed to break the palette, using a muted, desaturated
 * red reserved exclusively for genuine errors — never a neon alarm color.
 *
 * Renamed 1:1 from the retired `lib/shield-core/shieldCorePalette.ts`
 * (`SHIELD_PHASE_COLOR` -> `LIVING_CORE_PHASE_COLOR`), same values.
 */
export const LIVING_CORE_PHASE_COLOR: Record<LivingCorePhase, string> = {
  dormant: "#3d4650",
  idle: "#38bdf8",
  submitting: "#22d3ee",
  converged: "#8be9fd",
  unresolved: "#3b6675",
  fault: "#b3554f",
};

/** Metallic edge tokens for `ShieldOutline` — a cooler, less saturated
 * graphite/silver family than the point-cloud/connection cyan, so the
 * outline reads as a restrained metal edge the point cloud lives inside,
 * not a second glowing element competing with it. */
export const LIVING_CORE_SHIELD_COLOR: Record<LivingCorePhase, string> = {
  dormant: "#454d57",
  idle: "#9fb4c4",
  submitting: "#bfe3f2",
  converged: "#cfeaf5",
  unresolved: "#6b7f8c",
  fault: "#9c6b67",
};
