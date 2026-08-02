import type { ChatState } from "@/lib/state/chatMachine";
import type { HealthStatus } from "@/lib/types/health";

/**
 * The living-core's internal visual vocabulary. This is a *rendering*
 * concept, not a security concept — there is no "poisoned" or "defended"
 * state here, only "did the last request converge on grounded sources,
 * come back with none, or fail". Renamed 1:1 from the retired
 * `shield-core/shieldCoreState.ts` (`ShieldCorePhase` -> `LivingCorePhase`)
 * with identical behavior — do not change this derivation.
 */
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
 * The ONLY function allowed to read raw `ChatState`/`HealthStatus` fields
 * for living-core visual purposes. Every downstream component
 * (`ShieldOutline`, `NeuralPointCloud`, `NeuralConnections`,
 * `RetrievalScan`, `LivingCoreStaticFallback`, ...) receives only the
 * derived `LivingCorePhase` — plus, where relevant, a plain `SourceItem[]`
 * /count for `SourceNodes`/`RetrievalScan` and an optional error message
 * string for the fault caption — never the raw `ChatState` union itself.
 *
 * `healthStatus === "offline"` always wins: an offline backend means no
 * request can currently be in flight or have just succeeded, so the core
 * goes dormant regardless of whatever `chatState` still happens to hold
 * from before the backend dropped.
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

/**
 * Phases that keep the `frameloop="demand"` canvas continuously
 * invalidating (i.e. animate every frame). `dormant` (inert by design) and
 * `converged` (a settled, resolved state) render once per prop change and
 * then sit still until the phase itself changes again.
 */
export function isAnimatedPhase(phase: LivingCorePhase): boolean {
  return (
    phase === "idle" ||
    phase === "submitting" ||
    phase === "unresolved" ||
    phase === "fault"
  );
}
