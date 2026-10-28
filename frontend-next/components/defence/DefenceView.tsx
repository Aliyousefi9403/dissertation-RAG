"use client";

import type { ExperimentMode } from "@/components/experiment/ExperimentModeSelector";
import type { ChatState } from "@/lib/state/chatMachine";
import { ContextLens } from "@/components/defence/ContextLens";
import { MonitorMemoryPanel } from "@/components/defence/MonitorMemoryPanel";
import { MonitorTraceView } from "@/components/defence/MonitorTraceView";
import { RepairLedger } from "@/components/defence/RepairLedger";

/**
 * One distinct view per defence, so each shows how it actually works:
 *   Repaired   -> tracked-changes ledger of repaired words
 *   Contextual -> language-model lens: per-passage gauge and word heat
 *   Verified   -> runtime-monitor trace (rules, attempts, quarantine) and its memory
 * Defended keeps the entropy shield over the living core (`LivingCoreStage`).
 */
export function DefenceView({ mode, chatState }: { mode: ExperimentMode; chatState: ChatState }) {
  const done = chatState.status === "success" || chatState.status === "noSources";
  const sources = chatState.status === "success" ? chatState.sources : [];

  if (mode === "verified") {
    if (!done) return null;
    const refreshKey = `${chatState.question}|${chatState.latencyMs}`;
    return (
      <div className="defence-view-stack">
        {chatState.monitor && <MonitorTraceView trace={chatState.monitor} />}
        <MonitorMemoryPanel refreshKey={refreshKey} />
      </div>
    );
  }
  if (!done || sources.length === 0) {
    return null;
  }
  if (mode === "repaired") {
    return <RepairLedger sources={sources} />;
  }
  if (mode === "contextual") {
    return <ContextLens sources={sources} />;
  }
  return null;
}
