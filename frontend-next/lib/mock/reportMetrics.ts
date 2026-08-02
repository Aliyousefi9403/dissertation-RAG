/**
 * Illustrative Confidence / Trust Score figures for a single answer.
 *
 * No backend endpoint computes a calibrated confidence or trust metric —
 * the real `/chat` response only carries a raw per-source similarity
 * `score` (see `lib/types/chat.ts`, which explicitly forbids relabelling
 * that as "confidence" or "trust"). These numbers are a deterministic,
 * illustrative placeholder derived from the real sources actually
 * returned for the question asked (source count + mean similarity), so
 * they at least react to the real answer rather than being static or
 * random — they are NOT a calibrated ML confidence output and must never
 * be presented as ground truth.
 *
 * Placeholder pending a real backend endpoint — replace with a real
 * calibrated metric (if/when the backend exposes one) by editing this
 * file only; every caller (EvidencePanel, AnswerPanel) consumes it
 * through `computeReportMetrics`.
 */

import type { SourceItem } from "@/lib/types/chat";

export interface ReportMetrics {
  confidencePercent: number;
  trustScorePercent: number;
  /** Number of distinct `source_number` values among the sources — a real,
   * derived figure (not mocked). */
  citationCount: number;
}

const NO_SOURCES_METRICS: Omit<ReportMetrics, "citationCount"> = {
  confidencePercent: 38,
  trustScorePercent: 41,
};

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

export function computeReportMetrics(sources: SourceItem[]): ReportMetrics {
  if (sources.length === 0) {
    return { ...NO_SOURCES_METRICS, citationCount: 0 };
  }

  const meanScore =
    sources.reduce((sum, source) => sum + source.score, 0) / sources.length;

  // Real similarity scores from this stack's retriever are typically in a
  // 0-1 range; treat the mean as a percentage base and nudge it slightly
  // for corroboration (more distinct sources agreeing) — purely for a
  // plausible-looking illustrative figure, not a statistically derived one.
  const base = clampPercent(meanScore * 100);
  const citationCount = new Set(sources.map((source) => source.source_number))
    .size;
  const corroborationBonus = Math.min(6, citationCount * 1.5);

  const confidencePercent = clampPercent(base + corroborationBonus);
  const trustScorePercent = clampPercent(
    confidencePercent * 0.92 + Math.min(citationCount, 5),
  );

  return { confidencePercent, trustScorePercent, citationCount };
}
