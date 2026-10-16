"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";
import { useHealthStatus } from "@/hooks/useHealthStatus";
import { useChatSession } from "@/hooks/useChatSession";
import { useCompareSession } from "@/hooks/useCompareSession";
import { QueryComposer } from "@/components/composer/QueryComposer";
import { AnswerPanel } from "@/components/answer/AnswerPanel";
import { LivingCoreStage } from "@/components/living-core/LivingCoreStage";
import { PlatformStatusBar } from "@/components/status/PlatformStatusBar";
import { EvidencePanel } from "@/components/evidence/EvidencePanel";
import { ComparisonView } from "@/components/experiment/ComparisonView";
import {
  ExperimentModeSelector,
  type ExperimentMode,
} from "@/components/experiment/ExperimentModeSelector";
import { getLivingCorePhase } from "@/lib/living-core/livingCoreState";
import { getLivingCoreStatusText } from "@/lib/living-core/livingCoreCopy";
import { initialChatState } from "@/lib/state/chatMachine";

export default function Home() {
  const healthStatus = useHealthStatus();
  const { state, submitQuestion } = useChatSession();
  const { state: compareState, submitComparison } = useCompareSession();
  const [experimentMode, setExperimentMode] = useState<ExperimentMode>("clean");

  const isComparing = experimentMode === "compare";
  const composerBusy = isComparing
    ? compareState.status === "submitting"
    : state.status === "submitting";

  const composerDisabled = healthStatus !== "online" || composerBusy;

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
  // In Compare mode the same idle/active split is driven by the separate
  // `compareState` instead, since Compare never touches `useChatSession`.
  const isIdle = isComparing
    ? compareState.status === "idle"
    : state.status === "idle";
  const isSubmitting = composerBusy;

  // Same derivation `LivingCoreStage` uses internally for its own r3f
  // scene -- duplicated here (cheaply, from the same real `state`/
  // `healthStatus`) only to feed `PlatformStatusBar`'s status pill, which
  // replaced the old caption that used to render below the particle
  // canvas. Uses the same idle override as `LivingCoreStage` below while
  // comparing, so the status caption never contradicts what the particle
  // field is actually showing.
  const livingCoreChatState = isComparing ? initialChatState : state;
  const livingCorePhase = getLivingCorePhase(livingCoreChatState, healthStatus);
  const livingCoreSourceCount =
    livingCoreChatState.status === "success" ? livingCoreChatState.sources.length : 0;
  const livingCoreDetail =
    livingCoreChatState.status === "error" ? livingCoreChatState.message : undefined;
  const livingCoreStatusText = getLivingCoreStatusText(
    livingCorePhase,
    livingCoreSourceCount,
    livingCoreDetail,
  );

  function handleSubmit(question: string) {
    if (experimentMode === "compare") {
      void submitComparison(question);
      return;
    }

    void submitQuestion(question, experimentMode === "poisoned" ? "poisoned" : "clean");
  }

  return (
    <section className="workspace">
      <header className="topbar">
        <div>
          <p className="eyebrow">Assistant</p>
          <h2>Ask a grounded cybersecurity question</h2>
        </div>

        <ExperimentModeSelector mode={experimentMode} onChange={setExperimentMode} />
      </header>

      <PlatformStatusBar livingCoreStatusText={livingCoreStatusText} />

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
              <LivingCoreStage
                // Compare mode never feeds `useChatSession`'s `state`
                // (Compare uses the separate `useCompareSession`), so
                // without this override the Living Core would keep
                // showing whatever phase/sources were left over from the
                // last normal Clean/Poisoned question (e.g. stale
                // numbered SourcePins, a "converged" gold pulse) instead
                // of its plain idle/"alive" look. Forcing the real idle
                // state here reuses that already-correct rendering path
                // verbatim rather than duplicating it.
                chatState={isComparing ? initialChatState : state}
                healthStatus={healthStatus}
                attackDetected={experimentMode === "poisoned"}
                compareMode={isComparing}
              />
            </div>
          </div>

          {isComparing ? (
            <ComparisonView compareState={compareState} onRetry={handleSubmit} />
          ) : (
            <AnswerPanel chatState={state} onRetry={handleSubmit} />
          )}
        </div>

        {!isComparing && <EvidencePanel chatState={state} />}
      </div>

      <div className="composer-row">
        <QueryComposer
          onSubmit={handleSubmit}
          disabled={composerDisabled}
          isSubmitting={isSubmitting}
          placeholder={composerPlaceholder}
        />
      </div>
    </section>
  );
}
