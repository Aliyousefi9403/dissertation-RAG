"use client";

import { cn } from "@/lib/utils";
import { useHealthStatus } from "@/hooks/useHealthStatus";
import { useChatSession } from "@/hooks/useChatSession";
import { QueryComposer } from "@/components/composer/QueryComposer";
import { AnswerPanel } from "@/components/answer/AnswerPanel";
import { LivingCoreStage } from "@/components/living-core/LivingCoreStage";
import { PlatformStatusBar } from "@/components/status/PlatformStatusBar";
import { EvidencePanel } from "@/components/evidence/EvidencePanel";

export default function Home() {
  const healthStatus = useHealthStatus();
  const { state, submitQuestion } = useChatSession();

  const composerDisabled =
    healthStatus !== "online" || state.status === "submitting";

  const composerPlaceholder =
    healthStatus === "offline"
      ? "AegisRAG is offline. Waiting for the backend to reconnect…"
      : healthStatus === "checking"
        ? "Checking backend connection…"
        : "Message AegisRAG...";

  // Idle (no question asked yet) keeps the living core, quiet prompt and
  // composer/status as the sole visual focus, occupying most of the main
  // visual area. Once a question resolves — submitting, success,
  // noSources, or error — the core settles into a smaller, secondary role
  // and the answer/evidence stack becomes the dominant element (see
  // .conversation--idle/--active and .living-core-stage in globals.css).
  const isIdle = state.status === "idle";
  const isSubmitting = state.status === "submitting";

  function handleSubmit(question: string) {
    void submitQuestion(question);
  }

  return (
    <section className="workspace">
      <header className="topbar">
        <div>
          <p className="eyebrow">Assistant</p>
          <h2>Ask a grounded cybersecurity question</h2>
        </div>
      </header>

      <PlatformStatusBar />

      <div
        className={cn(
          "conversation",
          isIdle ? "conversation--idle" : "conversation--active",
        )}
      >
        <div className="conversation-main">
          <div
            className={cn(
              "living-core-stage",
              isIdle ? "living-core-stage--hero" : "living-core-stage--compact",
            )}
          >
            <div className="living-core-slot">
              <LivingCoreStage chatState={state} healthStatus={healthStatus} />
            </div>
          </div>

          <AnswerPanel chatState={state} onRetry={handleSubmit} />
        </div>

        <EvidencePanel chatState={state} />
      </div>

      {/* Mirrors `.conversation`'s main-column/evidence-column split (via
          `.composer-spacer`, same 340px reserved width) so the composer
          lines up with `.living-core-slot`/`.conversation-main` above it
          instead of centering across the full workspace width. */}
      <div className="composer-row">
        <div className="composer-column">
          <QueryComposer
            onSubmit={handleSubmit}
            disabled={composerDisabled}
            isSubmitting={isSubmitting}
            placeholder={composerPlaceholder}
          />
        </div>
        <div className="composer-spacer" aria-hidden="true" />
      </div>
    </section>
  );
}
