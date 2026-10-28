"use client";

import type { CompareState } from "@/lib/state/compareMachine";
import type { CompareSideResult } from "@/lib/types/compare";
import { UserQuestionCard } from "@/components/answer/AnswerPanel";
import { Markdown } from "@/components/answer/Markdown";
import { SourceCard } from "@/components/answer/SourceCard";
import { AttackMetrics } from "@/components/experiment/AttackMetrics";
import { Button } from "@/components/ui/button";

interface ComparisonViewProps {
  compareState: CompareState;
  onRetry: (question: string) => void;
}

function ComparisonSide({ label, result }: { label: string; result: CompareSideResult }) {
  return (
    <section className="comparison-side assistant-card">
      <p className="eyebrow">{label}</p>

      <div className="answer-text">
        <Markdown content={result.answer} />
      </div>

      {result.sources.length > 0 ? (
        <div className="source-list">
          {result.sources.map((source) => (
            <SourceCard key={`${source.source_number}-${source.source}`} source={source} />
          ))}
        </div>
      ) : (
        <p className="comparison-no-sources">No retrieved evidence.</p>
      )}
    </section>
  );
}

/**
 * Renders `POST /compare` results as two side-by-side panels plus the Attack Impact metrics
 * strip below them.
 */
export function ComparisonView({ compareState, onRetry }: ComparisonViewProps) {
  switch (compareState.status) {
    case "idle":
      return (
        <p className="idle-hint">
          Ask a question below to compare the clean and PWWS-poisoned knowledge base side by side.
        </p>
      );

    case "submitting":
      return (
        <div className="response-stack" key="submitting">
          <UserQuestionCard question={compareState.question} />

          <section className="assistant-card loading-card" aria-live="polite" aria-atomic="true">
            <div className="loading-orb" aria-hidden="true" />
            <div>
              <p className="eyebrow">AegisRAG pipeline</p>
              <h3>Comparing clean and PWWS-poisoned states…</h3>
            </div>
          </section>
        </div>
      );

    case "success": {
      const { result } = compareState;
      return (
        <div className="comparison-stack" key="success">
          <UserQuestionCard question={result.question} />

          <div className="comparison-grid">
            <ComparisonSide label="Clean baseline" result={result.clean} />
            <ComparisonSide label="PWWS poisoned" result={result.poisoned} />
          </div>

          <AttackMetrics
            metrics={result.metrics}
            attackQuality={result.attack_quality}
            retrievalQuality={result.retrieval_quality}
            generationQuality={result.generation_quality}
            attackSuccess={result.attack_success}
          />
        </div>
      );
    }

    case "error":
      return (
        <div className="response-stack" key="error">
          <UserQuestionCard question={compareState.question} />

          <section className="error-card" role="alert" aria-live="assertive">
            <strong>Something went wrong</strong>
            <p>{compareState.message}</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                onRetry(compareState.question);
              }}
            >
              Retry
            </Button>
          </section>
        </div>
      );

    default: {
      const exhaustiveCheck: never = compareState;
      return exhaustiveCheck;
    }
  }
}
