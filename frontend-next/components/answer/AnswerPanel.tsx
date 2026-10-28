"use client";

import type { ChatState } from "@/lib/state/chatMachine";
import { Button } from "@/components/ui/button";
import { Markdown } from "@/components/answer/Markdown";
import { ReportMetrics } from "@/components/answer/ReportMetrics";
import { EvidenceCheckCard } from "@/components/answer/EvidenceCheckCard";

interface AnswerPanelProps {
  chatState: ChatState;
  onRetry: (question: string) => void;
}

/** Exported for reuse by `components/experiment/ComparisonView.tsx`, which
 * needs the same "You" question card in Compare mode. */
export function UserQuestionCard({ question }: { question: string }) {
  return (
    <section className="user-card">
      <p className="eyebrow">You</p>
      <p>{question}</p>
    </section>
  );
}

function AnswerHeading() {
  return (
    <div className="assistant-heading">
      <div>
        <p className="eyebrow">AegisRAG</p>
        <h3>Grounded response</h3>
      </div>
    </div>
  );
}

function AnswerMarkdown({ answer }: { answer: string }) {
  return (
    // `key={answer}` forces a fresh DOM node each time a new, already-complete answer arrives.
    <div className="answer-text answer-reveal" key={answer}>
      <Markdown content={answer} />
    </div>
  );
}

export function AnswerPanel({ chatState, onRetry }: AnswerPanelProps) {
  switch (chatState.status) {
    case "idle":
      return (
        <p className="idle-hint">
          Ask a cybersecurity question below — AegisRAG will retrieve grounded evidence before it
          answers.
        </p>
      );

    case "submitting":
      return (
        <div className="response-stack" key="submitting">
          <UserQuestionCard question={chatState.question} />

          <section className="assistant-card loading-card" aria-live="polite" aria-atomic="true">
            <div className="loading-orb" aria-hidden="true" />
            <div>
              <p className="eyebrow">AegisRAG pipeline</p>
              <h3>Retrieving and analysing evidence</h3>
              <p>Searching the knowledge base and generating a response…</p>
            </div>
          </section>
        </div>
      );

    case "success": {
      const check = chatState.evidenceCheck;
      const withheld = check?.decision === "withheld";

      return (
        <div className="response-stack" key="success">
          <UserQuestionCard question={chatState.question} />

          <section className="assistant-card">
            <AnswerHeading />
            {withheld ? (
              <p className="answer-withheld">
                The draft answer was withheld by the experimental evidence check. See the result
                below.
              </p>
            ) : (
              <AnswerMarkdown answer={chatState.answer} />
            )}
            {check && <EvidenceCheckCard result={check} />}
            <ReportMetrics
              sources={chatState.sources}
              latencyMs={chatState.latencyMs}
              evidenceCheck={check}
            />
          </section>
        </div>
      );
    }

    case "noSources":
      if (chatState.evidenceCheck) {
        return (
          <div className="response-stack" key="noSources">
            <UserQuestionCard question={chatState.question} />

            <section className="assistant-card">
              <AnswerHeading />
              <EvidenceCheckCard result={chatState.evidenceCheck} />
              <ReportMetrics
                sources={[]}
                latencyMs={chatState.latencyMs}
                evidenceCheck={chatState.evidenceCheck}
              />
            </section>
          </div>
        );
      }

      return (
        <div className="response-stack" key="noSources">
          <UserQuestionCard question={chatState.question} />

          <section className="no-sources-card" role="status">
            <strong>No relevant sources were found in the knowledge base.</strong>
            <p>
              The answer below was generated without grounded evidence. Treat it with caution and
              verify independently.
            </p>
          </section>

          <section className="assistant-card">
            <AnswerHeading />
            <AnswerMarkdown answer={chatState.answer} />
            <ReportMetrics sources={[]} latencyMs={chatState.latencyMs} />
          </section>
        </div>
      );

    case "error":
      return (
        <div className="response-stack" key="error">
          <UserQuestionCard question={chatState.question} />

          <section className="error-card" role="alert" aria-live="assertive">
            <strong>Something went wrong</strong>
            <p>{chatState.message}</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                onRetry(chatState.question);
              }}
            >
              Retry
            </Button>
          </section>
        </div>
      );

    default: {
      const exhaustiveCheck: never = chatState;
      return exhaustiveCheck;
    }
  }
}
