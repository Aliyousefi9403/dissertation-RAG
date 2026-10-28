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
import { EvidenceCheckToggle } from "@/components/experiment/EvidenceCheckToggle";
import { TrustedFallbackToggle } from "@/components/defence/TrustedFallbackToggle";
import { DefenceView } from "@/components/defence/DefenceView";
import { getLivingCorePhase } from "@/lib/living-core/livingCoreState";
import { getLivingCoreStatusText } from "@/lib/living-core/livingCoreCopy";
import { initialChatState } from "@/lib/state/chatMachine";

export default function Home() {
  const healthStatus = useHealthStatus();
  const { state, submitQuestion } = useChatSession();
  const { state: compareState, submitComparison } = useCompareSession();
  const [experimentMode, setExperimentMode] = useState<ExperimentMode>("clean");
  const [evidenceCheckEnabled, setEvidenceCheckEnabled] = useState(false);
  const [trustedFallback, setTrustedFallback] = useState(false);

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

  // Idle keeps the living core, quiet prompt and composer/status as the sole visual focus.
  const isIdle = isComparing ? compareState.status === "idle" : state.status === "idle";
  const isSubmitting = composerBusy;

  // Same derivation `LivingCoreStage` uses internally for its own r3f scene.
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

    const systemState = experimentMode; // "compare" returned above

    void submitQuestion(question, systemState, {
      // The evidence check (`/guarded-chat`) supports clean/poisoned only.
      evidenceCheck:
        evidenceCheckEnabled && (systemState === "clean" || systemState === "poisoned"),
      trustedFallback: systemState === "verified" && trustedFallback,
    });
  }

  return (
    <section className="workspace">
      <header className="topbar">
        <div>
          <p className="eyebrow">Assistant</p>
          <h2>Ask a grounded cybersecurity question</h2>
        </div>

        <div className="topbar-controls">
          <ExperimentModeSelector mode={experimentMode} onChange={setExperimentMode} />
          {experimentMode === "verified" ? (
            <TrustedFallbackToggle enabled={trustedFallback} onChange={setTrustedFallback} />
          ) : (
            <EvidenceCheckToggle
              enabled={evidenceCheckEnabled}
              onChange={setEvidenceCheckEnabled}
              disabled={
                isComparing ||
                experimentMode === "defended" ||
                experimentMode === "repaired" ||
                experimentMode === "contextual"
              }
            />
          )}
        </div>
      </header>

      <PlatformStatusBar
        livingCoreStatusText={livingCoreStatusText}
        healthStatus={healthStatus}
        experimentMode={experimentMode}
        evidenceCheckEnabled={evidenceCheckEnabled}
      />

      <div className={cn("conversation", isIdle ? "conversation--idle" : "conversation--active")}>
        <div className="conversation-main">
          <div
            className={cn(
              "living-core-stage",
              isIdle ? "living-core-stage--hero" : "living-core-stage--compact",
            )}
          >
            <div className="living-core-slot">
              <LivingCoreStage
                // Compare mode never feeds `useChatSession`'s `state`.
                chatState={isComparing ? initialChatState : state}
                healthStatus={healthStatus}
                attackDetected={experimentMode === "poisoned"}
                compareMode={isComparing}
                defence={
                  experimentMode === "defended" ||
                  experimentMode === "repaired" ||
                  experimentMode === "contextual" ||
                  experimentMode === "verified"
                    ? experimentMode
                    : null
                }
                monitor={
                  state.status === "success" || state.status === "noSources" ? state.monitor : null
                }
              />
            </div>
          </div>

          {isComparing ? (
            <ComparisonView compareState={compareState} onRetry={handleSubmit} />
          ) : (
            <>
              <AnswerPanel chatState={state} onRetry={handleSubmit} />
              <DefenceView mode={experimentMode} chatState={state} />
            </>
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
