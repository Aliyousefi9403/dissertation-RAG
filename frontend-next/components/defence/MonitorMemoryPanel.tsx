"use client";

import { useEffect, useState } from "react";

import { getMonitorMemory, resetMonitorMemory } from "@/lib/api/monitor";
import type { MonitorMemory } from "@/lib/types/monitor";

/**
 * The runtime monitor's quarantine memory (`GET /monitor/memory`): every passage it has learned
 * not to trust, with the words that gave it away. Refreshes after each answer (`refreshKey`).
 * "Start fresh" archives the memory on the server; nothing is deleted.
 */
export function MonitorMemoryPanel({ refreshKey }: { refreshKey: string }) {
  const [memory, setMemory] = useState<MonitorMemory | null>(null);
  const [failed, setFailed] = useState(false);
  const [resets, setResets] = useState(0);

  useEffect(() => {
    let active = true;
    getMonitorMemory().then((result) => {
      if (!active) return;
      setFailed(result.kind !== "ok");
      if (result.kind === "ok") setMemory(result.data);
    });
    return () => {
      active = false;
    };
  }, [refreshKey, resets]);

  async function reset() {
    await resetMonitorMemory();
    setResets((n) => n + 1);
  }

  return (
    <aside className="monitor-memory" aria-label="Monitor memory" data-testid="monitor-memory">
      <div className="monitor-memory-head">
        <p className="eyebrow">Memory</p>
        <strong className="monitor-memory-count">{memory ? memory.count : "–"}</strong>
        <span>quarantined {memory?.count === 1 ? "passage" : "passages"}</span>
        <button type="button" className="monitor-memory-reset" onClick={() => void reset()} disabled={!memory || memory.count === 0}>
          Start fresh
        </button>
      </div>
      {failed && <p className="monitor-memory-empty">Memory unavailable</p>}
      {memory && memory.count === 0 && <p className="monitor-memory-empty">Nothing quarantined yet. Ask a question about a poisoned topic.</p>}
      {memory && memory.count > 0 && (
        <ul className="monitor-memory-list">
          {memory.entries.slice().reverse().map((e) => (
            <li key={e.key}>
              <span className="monitor-memory-source">{e.source}</span>
              {e.words.length > 0 && <span className="monitor-memory-words">{e.words.map((w) => <code key={w}>{w}</code>)}</span>}
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
