import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";

/** Single source of truth for the real, human-readable living-core status line. */
export function getLivingCoreStatusText(
  phase: LivingCorePhase,
  sourceCount: number,
  detail?: string,
): string {
  switch (phase) {
    case "dormant":
      return "Living core inactive — the backend is offline.";
    case "idle":
      return "Living core idle — ask a question to begin.";
    case "submitting":
      return "Living core retrieving and analysing your question…";
    case "converged":
      return `Living core resolved — grounded in ${sourceCount} ${
        sourceCount === 1 ? "source" : "sources"
      }.`;
    case "unresolved":
      return "Living core resolved — no matching sources were found in the knowledge base.";
    case "fault":
      return detail
        ? `Living core fault — ${detail}`
        : "Living core fault — the last request failed.";
    default: {
      const exhaustiveCheck: never = phase;
      return exhaustiveCheck;
    }
  }
}
