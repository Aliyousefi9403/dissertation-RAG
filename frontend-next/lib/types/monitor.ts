/** Types mirroring the runtime monitor's trace and `GET /monitor/memory`. */

export interface MonitorViolation {
  spec: "phi1_lexical" | "phi2_availability";
  detail: string;
  witnesses: string[];
}

export interface MonitorRound {
  round: number | "restore";
  skipped_quarantined?: number;
  context_keys?: string[];
  answer: string;
  violations: MonitorViolation[];
  quarantined?: string[];
  trusted_ids?: string;
}

export type MonitorOutcome = "released" | "released_refusal" | "restored" | "withheld";

export interface MonitorTrace {
  policy_version: string;
  mode: "verify" | "restore";
  attack: string | null;
  outcome: MonitorOutcome;
  rounds: MonitorRound[];
  generations: number;
  final_violations: MonitorViolation[];
  trusted_fallback: boolean;
}

export interface MonitorMemoryEntry {
  key: string;
  source: string | null;
  words: string[];
  specs: string[];
  question: string | null;
  round: number | null;
  at: number | null;
}

export interface MonitorMemory {
  policy_version: string;
  count: number;
  entries: MonitorMemoryEntry[];
}
