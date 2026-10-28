"use client";

import type { ExperimentMode } from "@/components/experiment/ExperimentModeSelector";
import type { ChatState } from "@/lib/state/chatMachine";
import { ContextLens } from "@/components/defence/ContextLens";
import { MonitorMemoryPanel } from "@/components/defence/MonitorMemoryPanel";
import { MonitorTraceView } from "@/components/defence/MonitorTraceView";
import { RepairLedger } from "@/components/defence/RepairLedger";

// Repaired: ledger of restored words. Contextual: per-passage lens.
// Verified: monitor trace and memory. Defended uses the shield over the core.
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
