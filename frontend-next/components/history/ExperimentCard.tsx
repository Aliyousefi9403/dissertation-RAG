import Link from "next/link";

import type { ExperimentRecord } from "@/lib/types/history";
import { Badge } from "@/components/ui/badge";

interface ExperimentCardProps {
  experiment: ExperimentRecord;
}

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(0)}%`;
}

function formatSignedScore(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(4)}`;
}

/**
 * One row in the Experiment History list. Reuses `.assistant-card`'s
 * surface (same titanium/cyan card language as the Assistant workspace)
 * with a small set of additive `.history-card*` layout classes on top —
 * see `app/globals.css`.
 */
export function ExperimentCard({ experiment }: ExperimentCardProps) {
  const isCompare = experiment.mode === "compare";

  const hasMetrics =
    experiment.retrieval_shift !== null ||
    experiment.top_k_overlap !== null ||
    experiment.top_score_delta !== null ||
    experiment.answer_changed !== null;

  return (
    <Link href={`/history/${experiment.id}`} className="history-card assistant-card">
      <div className="history-card-header">
        <p className="history-card-question">{experiment.question}</p>
        <span className="history-card-timestamp">{formatTimestamp(experiment.timestamp)}</span>
      </div>

      <div className="history-card-badges">
        <Badge variant="outline">{experiment.mode.toUpperCase()}</Badge>
        {experiment.attack_method && (
          <Badge variant="outline">{experiment.attack_method}</Badge>
        )}
      </div>

      {isCompare && hasMetrics && (
        <dl className="history-card-metrics">
          {experiment.retrieval_shift !== null && (
            <div>
              <dt>Retrieval Shift</dt>
              <dd>{formatPercent(experiment.retrieval_shift)}</dd>
            </div>
          )}
          {experiment.top_k_overlap !== null && (
            <div>
              <dt>Top-K Overlap</dt>
              <dd>{formatPercent(experiment.top_k_overlap)}</dd>
            </div>
          )}
          {experiment.top_score_delta !== null && (
            <div>
              <dt>Score Delta</dt>
              <dd>{formatSignedScore(experiment.top_score_delta)}</dd>
            </div>
          )}
          {experiment.answer_changed !== null && (
            <div>
              <dt>Answer Changed</dt>
              <dd>{experiment.answer_changed ? "YES" : "NO"}</dd>
            </div>
          )}
        </dl>
      )}

      <span className="history-card-link">View Experiment →</span>
    </Link>
  );
}
