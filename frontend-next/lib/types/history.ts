/** Types mirroring the backend Experiment History contract exactly. */
import type { SourceItem } from "@/lib/types/chat";
import type {
  AttackQualityMetrics,
  RetrievalQualityMetrics,
  GenerationQualityMetrics,
  AttackSuccessMetrics,
} from "@/lib/types/compare";

export type ExperimentMode = "clean" | "poisoned" | "compare" | "defended";

/** Mirrors the backend's single `research_metrics` JSON column. */
export interface ResearchMetrics {
  attack_quality?: AttackQualityMetrics | null;
  retrieval_quality?: RetrievalQualityMetrics | null;
  generation_quality?: GenerationQualityMetrics | null;
  attack_success?: AttackSuccessMetrics | null;
}

export interface ExperimentRecord {
  id: number;
  timestamp: string;
  question: string;
  mode: ExperimentMode;
  attack_method: string | null;

  clean_answer: string | null;
  poisoned_answer: string | null;
  defended_answer: string | null;

  clean_sources: SourceItem[] | null;
  poisoned_sources: SourceItem[] | null;
  defended_sources: SourceItem[] | null;

  clean_top_score: number | null;
  poisoned_top_score: number | null;
  defended_top_score: number | null;

  retrieval_shift: number | null;
  top_k_overlap: number | null;
  top_score_delta: number | null;
  shared_chunks: number | null;
  answer_changed: boolean | null;

  clean_latency: number | null;
  poisoned_latency: number | null;
  defended_latency: number | null;

  metadata: Record<string, unknown> | null;

  research_metrics: ResearchMetrics | null;
}

export interface ExperimentStats {
  total: number;
  clean: number;
  poisoned: number;
  compare: number;
  defended: number;
  answer_changed: number;
}

export interface HistoryFilters {
  mode?: ExperimentMode;
  attack_method?: string;
  answer_changed?: boolean;
  limit?: number;
}
