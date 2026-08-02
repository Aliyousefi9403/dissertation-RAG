/**
 * Mock platform status for the top status bar.
 *
 * No backend endpoint exists yet for platform-wide health/trust telemetry
 * (the real backend only exposes `GET /health` and `POST /chat` — see
 * `backend/app/main.py`). This module fakes a plausible response with the
 * same typed-async-function shape a real API client would have, so
 * swapping to a real `fetch()` later (e.g. `GET /api/platform/status`) is a
 * one-file change — nothing that imports `getPlatformStatus` needs to
 * change.
 *
 * Placeholder pending a real backend endpoint — swap this implementation
 * for a fetch() once /api/platform/status (or similar) exists.
 */

export type KnowledgeBaseHealth = "Healthy" | "Degraded";
export type SecurityStatus = "Nominal" | "Elevated";

export interface PlatformStatus {
  /** Illustrative platform-wide trust score, 0-100. Not a calibrated
   * metric — see `lib/mock/reportMetrics.ts` for the per-answer variant
   * that is at least reactive to real retrieval scores. */
  trustScorePercent: number;
  knowledgeBaseHealth: KnowledgeBaseHealth;
  documentsIndexed: number;
  activeLlm: string;
  securityStatus: SecurityStatus;
}

const MOCK_PLATFORM_STATUS: PlatformStatus = {
  trustScorePercent: 92,
  knowledgeBaseHealth: "Healthy",
  documentsIndexed: 214,
  // Matches the real default `LLM_MODEL` in `backend/app/config.py`
  // (overridable via the `LLM_MODEL` env var) — the one field here that
  // happens to be accurate rather than purely illustrative.
  activeLlm: "gpt-4o-mini",
  securityStatus: "Nominal",
};

/** Simulated network latency so loading states are actually exercised. */
const MOCK_LATENCY_MS = 260;

export async function getPlatformStatus(): Promise<PlatformStatus> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_LATENCY_MS));
  return { ...MOCK_PLATFORM_STATUS };
}
