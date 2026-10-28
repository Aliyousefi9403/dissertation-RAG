import type { MonitorTrace } from "@/lib/types/monitor";

/** Types mirroring the backend `/chat` contract exactly. */

/** "defended" = the PWWS-poisoned collection behind the entropy filter. */
export type SystemState =
  | "clean"
  | "poisoned"
  | "defended"
  | "repaired"
  | "contextual"
  | "verified";

export interface ChatRequest {
  question: string;
  system_state?: SystemState;
  /** Verified mode only: fall back to the trusted MITRE entry when a refusal cannot be fixed. */
  trusted_fallback?: boolean;
}

export interface SourceItem {
  source_number: number;
  source: string;
  /** Raw similarity score returned by the retriever. */
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
