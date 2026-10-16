import type { SourceItem } from "@/lib/types/chat";
import type { EvidenceCheckResult, EvidenceOutcome } from "@/lib/types/guardedChat";
import { countCitations, formatLatency } from "@/lib/evidence/citations";
import { Badge } from "@/components/ui/badge";

interface ReportMetricsProps {
  sources: SourceItem[];
  /** Real, measured latency for this answer's round trip. */
  latencyMs: number;
  /** Real evidence-check result, or null/undefined when none was run. */
  evidenceCheck?: EvidenceCheckResult | null;
}

export const EVIDENCE_OUTCOME_LABELS: Record<EvidenceOutcome, string> = {
  supported: "Supported",
  unsupported: "Unsupported",
  contradicted: "Contradicted",
  unavailable: "Unavailable",
  abstained: "Abstained",
};

/**
 * Compact report strip for the assistant's answer card. Every value is
 * measured or derived from the real response: latency, source/citation
 * counts and — only when one actually ran — the evidence-check outcome.
 * Nothing unmeasured (confidence, trust) is shown; the evidence check reads
 * "Not assessed" when the plain `/chat` route was used.
 */
export function ReportMetrics({ sources, latencyMs, evidenceCheck }: ReportMetricsProps) {
  const chunkCount = sources.length;
  const citationCount = countCitations(sources);

  const evidenceSummary =
    chunkCount === 0
      ? "No grounded evidence was retrieved for this question."
      : `Retrieved ${chunkCount} ${
          chunkCount === 1 ? "chunk" : "chunks"
        } across ${citationCount} ${
          citationCount === 1 ? "source" : "sources"
        }. Full excerpts, similarity scores and metadata are in the Evidence panel.`;

  return (
    <div className="report-metrics">
      <div className="report-chip-row" role="list" aria-label="Answer report summary">
        <Badge variant="outline" className="report-chip" role="listitem">
          Evidence check{" "}
          <strong data-outcome={evidenceCheck?.outcome ?? "not-assessed"}>
            {evidenceCheck ? EVIDENCE_OUTCOME_LABELS[evidenceCheck.outcome] : "Not assessed"}
          </strong>
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
            <dd>{citationCount}</dd>
          </div>
        </dl>
        <p className="report-evidence-summary">{evidenceSummary}</p>
      </details>
    </div>
  );
}
