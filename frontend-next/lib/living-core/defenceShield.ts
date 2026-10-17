import type { SourceItem } from "@/lib/types/chat";

interface EntropyVerdict {
  candidate_rank: number;
  repairs?: unknown[];
}

function verdictOf(source: SourceItem): EntropyVerdict | null {
  const value = source.metadata.entropy_filter;
  if (typeof value === "object" && value !== null && typeof (value as EntropyVerdict).candidate_rank === "number") {
    return value as EntropyVerdict;
  }
  return null;
}

/**
 * Number of retrieved candidates the entropy filter rejected *ahead of* the
 * passages it kept, derived only from real response data. Each kept source
 * carries its 1-based `candidate_rank` among the 10 candidates. Kept passages
 * are the first unflagged ones in rank order, so every rank below the last kept
 * rank that is not itself kept was flagged:
 *
 *   skipped = (highest kept rank) − (number of kept passages)
 *
 * Returns null when the response has no filter metadata (not Defended mode).
 */
export function skippedPassageCount(sources: SourceItem[]): number | null {
  const ranks = sources.map(verdictOf).filter((v): v is EntropyVerdict => v !== null).map((v) => v.candidate_rank);
  if (ranks.length === 0) {
    return null;
  }
  return Math.max(0, Math.max(...ranks) - ranks.length);
}

/** Words the repair policy replaced in the passages it kept (Repaired mode),
 * or null when the response has no filter metadata. */
export function repairedWordCount(sources: SourceItem[]): number | null {
  const verdicts = sources.map(verdictOf).filter((v): v is EntropyVerdict => v !== null);
  if (verdicts.length === 0) {
    return null;
  }
  return verdicts.reduce((total, v) => total + (Array.isArray(v.repairs) ? v.repairs.length : 0), 0);
}

export type ShieldState = "armed" | "scanning" | "resolved" | "fault";
