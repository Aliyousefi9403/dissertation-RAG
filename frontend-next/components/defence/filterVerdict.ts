import type { SourceItem } from "@/lib/types/chat";

/** The entropy / contextual filter's real decision for a kept passage
 * (`metadata.entropy_filter`, backend `app/defence/entropy_filter.py` and `contextual_filter.py`). */
export interface FilterVerdict {
  policy_version: string;
  candidate_rank: number;
  score_bits: number;
  threshold_bits: number;
  top_words?: Array<{ word: string; likely_original: string; gap_bits: number }>;
  score_before_repair_bits?: number;
  repairs?: Array<{ word: string; replacement: string; gap_bits: number }>;
}

export function verdictOf(source: SourceItem): FilterVerdict | null {
  const v = source.metadata.entropy_filter as FilterVerdict | undefined;
  return v && typeof v.score_bits === "number" && typeof v.threshold_bits === "number" ? v : null;
}

export function fileName(path: string): string {
  return path.replace(/\\/g, "/").split("/").slice(-2).join("/");
}
