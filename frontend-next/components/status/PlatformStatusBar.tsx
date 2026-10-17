"use client";

import type { HealthStatus } from "@/lib/types/health";
import type { ExperimentMode } from "@/components/experiment/ExperimentModeSelector";

interface PlatformStatusBarProps {
  /** The living core's real status line (`getLivingCoreStatusText`),
   * rendered as a small top-right pill. Keeps the exact className/role/aria
   * attributes so `e2e/desktop.spec.ts`'s `.living-core-status-caption`
   * locator still resolves. */
  livingCoreStatusText: string;
  /** Real backend reachability from `useHealthStatus` (`GET /health`). */
  healthStatus: HealthStatus;
  /** The knowledge base the next question will actually use. */
  experimentMode: ExperimentMode;
  /** Whether the next Clean/Poisoned question goes through the evidence
   * check (`POST /guarded-chat`). */
  evidenceCheckEnabled: boolean;
}

const HEALTH_LABELS: Record<HealthStatus, string> = {
  checking: "Checking…",
  online: "Reachable",
  offline: "Unreachable",
};

const MODE_LABELS: Record<ExperimentMode, string> = {
  clean: "Clean baseline",
  poisoned: "PWWS poisoned",
  compare: "Clean vs PWWS poisoned",
  defended: "PWWS poisoned + entropy filter",
  repaired: "PWWS poisoned + entropy repair",
};

const EVIDENCE_CHECK_UNAVAILABLE: Partial<Record<ExperimentMode, string>> = {
  compare: "Compare",
  defended: "Defended",
  repaired: "Repaired",
};

/**
 * Top-of-workspace status strip. Shows only values the interface actually
 * knows: backend reachability (real `GET /health`), the selected knowledge
 * base and whether the evidence check is on. Platform-wide trust, security
 * and knowledge-base health are not measured anywhere, so they read
 * "Not assessed" rather than showing invented figures.
 */
export function PlatformStatusBar({
  livingCoreStatusText,
  healthStatus,
  experimentMode,
  evidenceCheckEnabled,
}: PlatformStatusBarProps) {
  const unavailableIn = EVIDENCE_CHECK_UNAVAILABLE[experimentMode];
  const evidenceCheckLabel = unavailableIn
    ? `Not available in ${unavailableIn}`
    : evidenceCheckEnabled
        ? "On (experimental)"
        : "Off";

  return (
    <div className="platform-status-bar" role="status" aria-label="Platform status">
      <div className="platform-status-item">
        <span className="platform-status-label">Backend</span>
        <span
          className={
            healthStatus === "online"
              ? "platform-status-value platform-status-value--ok"
              : healthStatus === "offline"
                ? "platform-status-value platform-status-value--warn"
                : "platform-status-value"
          }
        >
          {HEALTH_LABELS[healthStatus]}
        </span>
      </div>

      <div className="platform-status-item">
        <span className="platform-status-label">Knowledge base</span>
        <span className="platform-status-value">{MODE_LABELS[experimentMode]}</span>
      </div>

      <div className="platform-status-item">
        <span className="platform-status-label">Evidence check</span>
        <span
          className={
            evidenceCheckEnabled && !unavailableIn
              ? "platform-status-value platform-status-value--accent"
              : "platform-status-value"
          }
        >
          {evidenceCheckLabel}
        </span>
      </div>

      <div className="platform-status-item">
        <span className="platform-status-label">Corpus integrity</span>
        <span className="platform-status-value platform-status-value--muted">Not assessed</span>
      </div>

      <p
        className="living-core-status-caption"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {livingCoreStatusText}
      </p>
    </div>
  );
}
