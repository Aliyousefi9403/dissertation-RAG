import type { ChatState } from "@/lib/state/chatMachine";
import { countCitations, formatLatency } from "@/lib/evidence/citations";
import { EVIDENCE_OUTCOME_LABELS } from "@/components/answer/ReportMetrics";
import { SourceCard } from "@/components/answer/SourceCard";

interface EvidencePanelProps {
  chatState: ChatState;
}

function EvidenceMetric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="evidence-metric">
      <dt>{label}</dt>
      <dd>{value}</dd>
      {hint && <p className="evidence-metric-hint">{hint}</p>}
    </div>
  );
}

/** Right-hand evidence column for the Assistant workspace. */
export function EvidencePanel({ chatState }: EvidencePanelProps) {
  if (chatState.status === "idle") {
    return (
      <aside className="evidence-column" aria-label="Evidence panel">
        <div className="evidence-empty">
          <p className="eyebrow">Evidence</p>
          <p>Evidence will appear here once you ask a question.</p>
        </div>
      </aside>
    );
  }

  if (chatState.status === "submitting") {
    return (
      <aside className="evidence-column" aria-label="Evidence panel">
        <div className="evidence-empty" aria-live="polite">
          <p className="eyebrow">Evidence</p>
          <p>Retrieving evidence from the knowledge base…</p>
        </div>
      </aside>
    );
  }

  if (chatState.status === "error") {
    return (
      <aside className="evidence-column" aria-label="Evidence panel">
        <div className="evidence-empty">
          <p className="eyebrow">Evidence</p>
          <p>No evidence available — the last request failed.</p>
        </div>
      </aside>
    );
  }

  // success | noSources
  const sources = chatState.status === "success" ? chatState.sources : [];
  const check = chatState.evidenceCheck;

  return (
    <aside className="evidence-column" aria-label="Evidence panel">
      <dl className="evidence-metrics">
        <EvidenceMetric
          label="Evidence check"
          value={check ? EVIDENCE_OUTCOME_LABELS[check.outcome] : "Not assessed"}
          hint={
            check
              ? "Experimental: whether the sources state the claims — not proof they are true."
              : undefined
          }
        />
        <EvidenceMetric label="Citations" value={String(countCitations(sources))} />
        <EvidenceMetric label="Latency" value={formatLatency(chatState.latencyMs)} />
      </dl>

      {sources.length > 0 ? (
        <section className="evidence-section" aria-label="Retrieved evidence sources">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Retrieval trace</p>
              <h3>Evidence chain</h3>
            </div>

            <span>
              {sources.length} {sources.length === 1 ? "source" : "sources"}
            </span>
          </div>

          <div className="source-list">
            {sources.map((source) => (
              <SourceCard key={`${source.source_number}-${source.source}`} source={source} />
            ))}
          </div>
        </section>
      ) : (
        <div className="evidence-empty">
          <p>No retrieved chunks — the answer was generated without grounded evidence.</p>
        </div>
      )}
    </aside>
  );
}
