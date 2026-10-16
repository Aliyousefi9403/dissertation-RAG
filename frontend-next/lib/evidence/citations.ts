import type { SourceItem } from "@/lib/types/chat";

/** Number of distinct retrieved sources — a real, derived count. */
export function countCitations(sources: SourceItem[]): number {
  return new Set(sources.map((source) => source.source_number)).size;
}

export function formatLatency(latencyMs: number): string {
  if (latencyMs < 1000) {
    return `${Math.round(latencyMs)} ms`;
  }
  return `${(latencyMs / 1000).toFixed(2)} s`;
}
