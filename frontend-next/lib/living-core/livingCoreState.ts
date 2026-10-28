import type { ChatState } from "@/lib/state/chatMachine";
import type { HealthStatus } from "@/lib/types/health";

/** The living-core's internal visual vocabulary. */
export type LivingCorePhase =
  | "dormant"
  | "idle"
  | "submitting"
  | "converged"
  | "unresolved"
  | "fault";

function assertNever(value: never): never {
  throw new Error(`Unhandled chat status: ${JSON.stringify(value)}`);
}

/**
 * The ONLY function allowed to read raw `ChatState`/`HealthStatus` fields for living-core
 * visual purposes.
 */
export function getLivingCorePhase(
  chatState: ChatState,
  healthStatus: HealthStatus,
): LivingCorePhase {
  if (healthStatus === "offline") {
    return "dormant";
  }

  switch (chatState.status) {
    case "idle":
      return "idle";
    case "submitting":
      return "submitting";
    case "success":
      return "converged";
    case "noSources":
      return "unresolved";
    case "error":
      return "fault";
    default:
      return assertNever(chatState);
  }
}

/** Phases that keep the `frameloop="demand"` canvas continuously invalidating. */
export function isAnimatedPhase(phase: LivingCorePhase): boolean {
  return phase === "idle" || phase === "submitting" || phase === "unresolved" || phase === "fault";
}
