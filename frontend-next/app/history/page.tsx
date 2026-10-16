"use client";

import { useEffect, useMemo, useState } from "react";

import { listHistory } from "@/lib/api/history";
import type { ExperimentMode, ExperimentRecord } from "@/lib/types/history";
import { ExperimentCard } from "@/components/history/ExperimentCard";

type LoadState = "loading" | "ready" | "error";
type ModeFilter = "all" | ExperimentMode;

const MODE_FILTERS: Array<{ value: ModeFilter; label: string }> = [
  { value: "all", label: "All" },
  { value: "clean", label: "Clean" },
  { value: "poisoned", label: "Poisoned" },
  { value: "compare", label: "Compare" },
  { value: "defended", label: "Defended" },
];

/**
 * Experiment History — recorded runs of the Assistant's Clean/Poisoned/
 * Compare queries, saved automatically by the backend (see
 * `backend/app/history/`). Same page shell as `/knowledge-base`
 * (`.workspace`/`.topbar`/`.kb-content`), same filter-chip visual as the
 * Assistant's experiment-mode selector (`.experiment-mode-button`) — no
 * new page chrome introduced.
 */
export default function HistoryPage() {
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [modeFilter, setModeFilter] = useState<ModeFilter>("all");
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;

    const timeoutId = setTimeout(() => {
      if (cancelled) return;
      setLoadState((prev) => (prev === "ready" ? "ready" : "loading"));

      listHistory({
        mode: modeFilter === "all" ? undefined : modeFilter,
        limit: 100,
      })
        .then((result) => {
          if (cancelled) return;
          if (result.kind === "ok") {
            setExperiments(result.data);
            setLoadState("ready");
          } else {
            setLoadState("error");
          }
        })
        .catch(() => {
          if (!cancelled) setLoadState("error");
        });
    }, 0);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [modeFilter]);

  const filtered = useMemo(() => {
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) return experiments;
    return experiments.filter((experiment) =>
      experiment.question.toLowerCase().includes(trimmed),
    );
  }, [experiments, query]);

  return (
    <section className="workspace">
      <header className="topbar">
        <div>
          <p className="eyebrow">Experiment History</p>
          <h2>Recorded Clean, Poisoned and Comparison runs</h2>
        </div>
      </header>

      <div className="kb-content">
        <div className="kb-toolbar">
          <div className="experiment-mode-row" role="tablist" aria-label="Filter by mode">
            {MODE_FILTERS.map((filter) => (
              <button
                key={filter.value}
                type="button"
                role="tab"
                aria-selected={modeFilter === filter.value}
                data-active={modeFilter === filter.value}
                className="experiment-mode-button"
                onClick={() => setModeFilter(filter.value)}
              >
                {filter.label}
              </button>
            ))}
          </div>

          <div className="kb-search">
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by question…"
              aria-label="Search experiment history by question"
            />
          </div>
        </div>

        {loadState === "ready" && (
          <span className="kb-count">
            {filtered.length} {filtered.length === 1 ? "experiment" : "experiments"}
          </span>
        )}

        {loadState === "loading" && (
          <p className="kb-empty" aria-live="polite">
            Loading experiment history…
          </p>
        )}

        {loadState === "error" && (
          <p className="kb-empty kb-empty--error" role="alert">
            Could not load experiment history. Make sure the backend is running.
          </p>
        )}

        {loadState === "ready" && filtered.length === 0 && (
          <p className="kb-empty">
            {query
              ? `No experiments match "${query}".`
              : "No experiments recorded yet — ask a question on the Assistant page."}
          </p>
        )}

        {loadState === "ready" && filtered.length > 0 && (
          <div className="history-list">
            {filtered.map((experiment) => (
              <ExperimentCard key={experiment.id} experiment={experiment} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
