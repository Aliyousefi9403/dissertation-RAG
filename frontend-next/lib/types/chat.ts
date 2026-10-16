/**
 * Types mirroring the backend `/chat` contract exactly.
 * See backend/app/main.py (ChatRequest, SourceResponse, ChatResponse).
 * Do not add fields that are not present in the backend response.
 */

export type SystemState = "clean" | "poisoned";

export interface ChatRequest {
  question: string;
  system_state?: SystemState;
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
}
