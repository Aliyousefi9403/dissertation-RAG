import type { SourceItem } from "@/lib/types/chat";
import { computeReportMetrics } from "@/lib/mock/reportMetrics";
import { Badge } from "@/components/ui/badge";

interface ReportMetricsProps {
  sources: SourceItem[];
  /** Real, measured latency for this answer's `POST /chat` round trip. */
  latencyMs: number;
}

function formatLatency(latencyMs: number): string {
  if (latencyMs < 1000) {
    return `${Math.round(latencyMs)} ms`;
  }
  return `${(latencyMs / 1000).toFixed(2)} s`;
}

/**
 * Compact "security report" strip for the assistant's answer card
 * (`AnswerPanel`'s success/noSources cases): a badge row for the figures
 * worth seeing at a glance (Confidence, Trust Score, Latency, source
 * count), plus an expandable `<details>` block for the denser secondary
 * figures (retrieved chunks, citations, a short evidence summary) — the
 * full per-source list itself lives only in `EvidencePanel` (Task 2) to
 * avoid rendering the same list twice on screen.
 *
 * Confidence/Trust Score are illustrative mock figures derived from the
 * real sources for this answer (`lib/mock/reportMetrics.ts`); Latency and
 * the source/chunk/citation counts are real.
 */
export function ReportMetrics({ sources, latencyMs }: ReportMetricsProps) {
  const metrics = computeReportMetrics(sources);
  const chunkCount = sources.length;

  const evidenceSummary =
    chunkCount === 0
      ? "No grounded evidence was retrieved for this question."
      : `Grounded in ${chunkCount} retrieved ${
          chunkCount === 1 ? "chunk" : "chunks"
        } across ${metrics.citationCount} cited ${
          metrics.citationCount === 1 ? "source" : "sources"
        }. Full excerpts, similarity scores and metadata are in the Evidence panel.`;

  return (
    <div className="report-metrics">
      <div className="report-chip-row" role="list" aria-label="Answer report summary">
        <Badge variant="outline" className="report-chip" role="listitem">
          Confidence <strong>{metrics.confidencePercent}%</strong>
        </Badge>
        <Badge variant="outline" className="report-chip" role="listitem">
          Trust score <strong>{metrics.trustScorePercent}%</strong>
        </Badge>
        <Badge variant="outline" className="report-chip" role="listitem">
          Latency <strong>{formatLatency(latencyMs)}</strong>
        </Badge>
        <Badge variant="outline" className="report-chip" role="listitem">
          {chunkCount} {chunkCount === 1 ? "source" : "sources"}
        </Badge>
      </div>

      <details className="report-details">
        <summary>Report details</summary>
        <dl className="report-details-grid">
          <div>
            <dt>Retrieved chunks</dt>
            <dd>{chunkCount}</dd>
          </div>
          <div>
            <dt>Citations</dt>
            <dd>{metrics.citationCount}</dd>
          </div>
        </dl>
        <p className="report-evidence-summary">{evidenceSummary}</p>
      </details>
    </div>
  );
}
