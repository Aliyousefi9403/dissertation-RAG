/** Types mirroring the backend `POST /compare` contract exactly. */
import type { SourceItem, SystemState } from "@/lib/types/chat";

export interface CompareRequest {
  question: string;
}

export interface CompareSideResult {
  question: string;
  answer: string;
  sources: SourceItem[];
  system_state: SystemState;
}

export interface CompareMetrics {
  attack_method: string;
  top_k: number;
  top_k_overlap: number;
  retrieval_shift: number;
  clean_top_score: number;
  poisoned_top_score: number;
  top_score_delta: number;
  answer_changed: boolean;
  shared_chunks: number;
  clean_source_ids: unknown[];
  poisoned_source_ids: unknown[];
  clean_attack_types: unknown[];
  poisoned_attack_types: unknown[];
}

export interface AttackQualityMetrics {
  mean_modification_rate: number | null;
  mean_semantic_similarity: number | null;
}

export interface RetrievalQualityMetrics {
  poison_hit_at_3: number | null;
  poisoned_chunks_in_top_3: number | null;
  poisoned_chunk_ranks: number[] | null;
  clean_hit_at_3: number | null;
  poisoned_hit_at_3: number | null;
  clean_reciprocal_rank: number | null;
  poisoned_reciprocal_rank: number | null;
}

export interface GenerationQualityMetrics {
  clean_answer_correctness: number | null;
  poisoned_answer_correctness: number | null;
  clean_answer_correctness_reason: string | null;
  poisoned_answer_correctness_reason: string | null;
  answer_correctness_delta: number | null;
  clean_faithfulness: number | null;
  poisoned_faithfulness: number | null;
  clean_faithfulness_reason: string | null;
  poisoned_faithfulness_reason: string | null;
  faithfulness_delta: number | null;
}

export interface AttackSuccessMetrics {
  rag_attack_success: boolean | null;
  correctness_drop: number | null;
  success_threshold: number | null;
  rag_attack_success_reason: string | null;
}

export interface CompareResponse {
  question: string;
  clean: CompareSideResult;
  poisoned: CompareSideResult;
  metrics: CompareMetrics;
  attack_quality?: AttackQualityMetrics | null;
  retrieval_quality?: RetrievalQualityMetrics | null;
  generation_quality?: GenerationQualityMetrics | null;
  attack_success?: AttackSuccessMetrics | null;
}
