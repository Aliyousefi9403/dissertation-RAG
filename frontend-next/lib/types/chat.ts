import type { MonitorTrace } from "@/lib/types/monitor";

/**
 * Types mirroring the backend `/chat` contract exactly.
 * See backend/app/main.py (ChatRequest, SourceResponse, ChatResponse).
 * Do not add fields that are not present in the backend response.
 */

/** "defended" = the PWWS-poisoned collection behind the entropy filter;
 * "contextual" = the same collection behind the language-model (contextual) filter;
 * "repaired" = the same collection behind repair-then-rescore;
 * "verified" = the same collection under the runtime verification monitor. */
export type SystemState = "clean" | "poisoned" | "defended" | "repaired" | "contextual" | "verified";

export interface ChatRequest {
  question: string;
  system_state?: SystemState;
  /** Verified mode only: fall back to the trusted MITRE entry when a refusal cannot be fixed. */
  trusted_fallback?: boolean;
}

export interface SourceItem {
  source_number: number;
  source: string;
  /**
   * Raw similarity score returned by the retriever. This is NOT a
   * calibrated confidence value. Always label it "similarity score"
   * in the UI; never "confidence" or "trust".
   */
  score: number;
  content: string;
  metadata: Record<string, unknown>;
}

export interface ChatResponse {
  question: string;
  answer: string;
  sources: SourceItem[];
  /** Verified mode only: the runtime monitor's trace; absent or null otherwise. */
  monitor?: MonitorTrace | null;
}
