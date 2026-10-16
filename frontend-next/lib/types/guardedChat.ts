/**
 * Types mirroring the experimental backend `POST /guarded-chat` contract
 * exactly. See backend/app/defence/router.py (GuardedChatResponse).
 *
 * This is an experimental evidence-support baseline, NOT a validated poison
 * detector: "supported" only means the retrieved sources state the claim,
 * and a poisoned source can support a false answer. There is deliberately
 * no confidence/trust percentage anywhere in this contract.
 */

import type { SourceItem, SystemState } from "@/lib/types/chat";

export type EvidenceOutcome =
  | "supported"
  | "unsupported"
  | "contradicted"
  | "unavailable"
  | "abstained";
export type EvidenceVerdict = "supported" | "unsupported" | "contradicted";
export type ReleaseDecision = "released" | "withheld";

export interface GuardedChatRequest {
  question: string;
  system_state: SystemState;
}

export interface EvidenceQuote {
  source_id: string;
  text: string;
  /** True only if the quotation was found verbatim in the cited source. */
  verified: boolean;
}

export interface EvidenceClaim {
  claim: string;
  /** Final status after quotation checks (may be "unavailable"). */
  status: EvidenceOutcome;
  /** What the verifier model itself said, before quotation checks. */
  verifier_verdict: EvidenceVerdict;
  source_ids: string[];
  quotes: EvidenceQuote[];
  explanation: string;
  problems: string[];
}

export interface GuardedSourceItem extends SourceItem {
  source_id: string;
}

export interface EvidenceFailure {
  stage: string;
  type: string;
  timeout: boolean;
}

export interface EvidenceAudit {
  saved: boolean;
  run_id: string;
  location: string | null;
  error: string | null;
}

export interface GuardedChatResponse {
  run_id: string;
  question: string;
  system_state: SystemState;
  policy_version: string;
  label: string;
  outcome: EvidenceOutcome;
  decision: ReleaseDecision;
  /** Present only when the draft was released. */
  answer: string | null;
  explanation: string;
  claims: EvidenceClaim[];
  sources: GuardedSourceItem[];
  failures: EvidenceFailure[];
  audit: EvidenceAudit;
  timings_ms: Record<string, number | null>;
}

/** The subset of a guarded response the chat UI keeps alongside an answer. */
export type EvidenceCheckResult = Omit<GuardedChatResponse, "question" | "answer" | "sources">;
