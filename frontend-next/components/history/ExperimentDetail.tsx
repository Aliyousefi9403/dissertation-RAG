import type { ExperimentRecord } from "@/lib/types/history";
import type { CompareMetrics } from "@/lib/types/compare";
import { Markdown } from "@/components/answer/Markdown";
import { SourceCard } from "@/components/answer/SourceCard";
import { AttackMetrics } from "@/components/experiment/AttackMetrics";

interface ExperimentDetailProps {
  experiment: ExperimentRecord;
}

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function formatLatency(latencyMs: number): string {
  if (latencyMs < 1000) {
    return `${Math.round(latencyMs)} ms`;
  }
  return `${(latencyMs / 1000).toFixed(2)} s`;
}

/** Single-sided (CLEAN, POISONED, or future DEFENDED) result panel —
 * reuses `.assistant-card`/`.answer-text`/`.source-list`/`SourceCard`
 * verbatim, the same visual language as the normal Assistant answer. */
function SingleResultPanel({
  label,
  answer,
  sources,
  topScore,
  latencyMs,
}: {
  label: string;
  answer: string | null;
  sources: ExperimentRecord["clean_sources"];
  topScore: number | null;
  latencyMs: number | null;
}) {
  return (
    <div className="response-stack">
      <section className="assistant-card">
        <p className="eyebrow">{label}</p>
        <div className="answer-text">
          <Markdown content={answer ?? ""} />
        </div>

        <div className="report-metrics">
          <div className="report-chip-row" role="list" aria-label="Result summary">
            {topScore !== null && (
              <span className="report-chip">
                Top score <strong>{topScore.toFixed(4)}</strong>
              </span>
            )}
            {latencyMs !== null && (
              <span className="report-chip">
                Latency <strong>{formatLatency(latencyMs)}</strong>
              </span>
            )}
          </div>
        </div>
      </section>

      {sources && sources.length > 0 && (
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
      )}
    </div>
  );
}

/** Experiment History detail view. */
export function ExperimentDetail({ experiment }: ExperimentDetailProps) {
  if (experiment.mode === "compare") {
    const metrics: CompareMetrics = {
      attack_method: experiment.attack_method ?? "PWWS",
      top_k: Math.max(
        experiment.clean_sources?.length ?? 0,
        experiment.poisoned_sources?.length ?? 0,
      ),
      top_k_overlap: experiment.top_k_overlap ?? 0,
      retrieval_shift: experiment.retrieval_shift ?? 0,
      clean_top_score: experiment.clean_top_score ?? 0,
      poisoned_top_score: experiment.poisoned_top_score ?? 0,
      top_score_delta: experiment.top_score_delta ?? 0,
      answer_changed: experiment.answer_changed ?? false,
      shared_chunks: experiment.shared_chunks ?? 0,
      clean_source_ids: [],
      poisoned_source_ids: [],
      clean_attack_types: [],
      poisoned_attack_types: [],
    };

    return (
      <div className="comparison-stack">
        <section className="user-card">
          <p className="eyebrow">Recorded question</p>
          <p>{experiment.question}</p>
        </section>

        <div className="comparison-grid">
          <section className="comparison-side assistant-card">
            <p className="eyebrow">Clean Baseline</p>
            <div className="answer-text">
              <Markdown content={experiment.clean_answer ?? ""} />
            </div>
            {experiment.clean_sources && experiment.clean_sources.length > 0 ? (
              <div className="source-list">
                {experiment.clean_sources.map((source) => (
                  <SourceCard key={`${source.source_number}-${source.source}`} source={source} />
                ))}
              </div>
            ) : (
              <p className="comparison-no-sources">No retrieved evidence.</p>
            )}
          </section>

          <section className="comparison-side assistant-card">
            <p className="eyebrow">PWWS Poisoned</p>
            <div className="answer-text">
              <Markdown content={experiment.poisoned_answer ?? ""} />
            </div>
            {experiment.poisoned_sources && experiment.poisoned_sources.length > 0 ? (
              <div className="source-list">
                {experiment.poisoned_sources.map((source) => (
                  <SourceCard key={`${source.source_number}-${source.source}`} source={source} />
                ))}
              </div>
            ) : (
              <p className="comparison-no-sources">No retrieved evidence.</p>
            )}
          </section>
        </div>

        <AttackMetrics
          metrics={metrics}
          attackQuality={experiment.research_metrics?.attack_quality}
          retrievalQuality={experiment.research_metrics?.retrieval_quality}
          generationQuality={experiment.research_metrics?.generation_quality}
          attackSuccess={experiment.research_metrics?.attack_success}
        />
      </div>
    );
  }

  const label =
    experiment.mode === "clean"
      ? "Clean Baseline"
      : experiment.mode === "poisoned"
        ? "PWWS Poisoned"
        : "Defended";

  const answer =
    experiment.mode === "clean"
      ? experiment.clean_answer
      : experiment.mode === "poisoned"
        ? experiment.poisoned_answer
        : experiment.defended_answer;

  const sources =
    experiment.mode === "clean"
      ? experiment.clean_sources
      : experiment.mode === "poisoned"
        ? experiment.poisoned_sources
        : experiment.defended_sources;

  const topScore =
    experiment.mode === "clean"
      ? experiment.clean_top_score
      : experiment.mode === "poisoned"
        ? experiment.poisoned_top_score
        : experiment.defended_top_score;

  const latencyMs =
    experiment.mode === "clean"
      ? experiment.clean_latency
      : experiment.mode === "poisoned"
        ? experiment.poisoned_latency
        : experiment.defended_latency;

  return (
    <div className="response-stack">
      <section className="user-card">
        <p className="eyebrow">Recorded question</p>
        <p>{experiment.question}</p>
      </section>

      <SingleResultPanel
        label={label}
        answer={answer}
        sources={sources}
        topScore={topScore}
        latencyMs={latencyMs}
      />
    </div>
  );
}

export { formatTimestamp };
