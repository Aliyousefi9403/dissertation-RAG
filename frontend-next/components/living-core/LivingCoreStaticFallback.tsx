import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";
import { getLivingCoreStatusText } from "@/lib/living-core/livingCoreCopy";
import { buildShieldSvgPath } from "@/lib/living-core/shieldGeometry";
import type { SourceItem } from "@/lib/types/chat";

interface LivingCoreStaticFallbackProps {
  phase: LivingCorePhase;
  sources: SourceItem[];
  detail?: string;
}

const PHASE_HEADING: Record<LivingCorePhase, string> = {
  dormant: "Living core inactive",
  idle: "Living core ready",
  submitting: "Living core analysing",
  converged: "Living core resolved",
  unresolved: "Living core resolved (no sources)",
  fault: "Living core fault",
};

// Same silhouette description the 3D `ShieldOutline` traces, rendered flat as an SVG path.
const SHIELD_SVG_PATH = buildShieldSvgPath(64, 4);

/** Pure DOM/CSS living-core presentation. */
export function LivingCoreStaticFallback({
  phase,
  sources,
  detail,
}: LivingCoreStaticFallbackProps) {
  const visibleSources = phase === "converged" ? sources : [];

  return (
    <div className="living-core-fallback" role="status" aria-live="polite" aria-atomic="true">
      <svg
        className="living-core-glyph"
        data-phase={phase}
        viewBox="0 0 64 64"
        aria-hidden="true"
        focusable="false"
      >
        <path d={SHIELD_SVG_PATH} />
      </svg>
      <div className="living-core-fallback-text">
        <h3>{PHASE_HEADING[phase]}</h3>
        <p>{getLivingCoreStatusText(phase, sources.length, detail)}</p>
        {visibleSources.length > 0 && (
          <ul className="living-core-source-list" aria-label="Sources grounding this answer">
            {visibleSources.map((source) => (
              <li key={source.source_number} className="living-core-source-item">
                <span className="living-core-source-number" aria-hidden="true">
                  {source.source_number}
                </span>
                <span className="living-core-source-name">{source.source}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
