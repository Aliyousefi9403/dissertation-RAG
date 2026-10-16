"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { getHistoryEntry } from "@/lib/api/history";
import type { ExperimentRecord } from "@/lib/types/history";
import { ExperimentDetail } from "@/components/history/ExperimentDetail";

type LoadState = "loading" | "ready" | "error" | "not-found";

/** Experiment History detail route (`/history/[id]`) — reopens one
 * recorded experiment exactly as it looked when saved. Same page shell as
 * the list page; rendering itself is delegated to `ExperimentDetail`. */
export default function HistoryDetailPage() {
  const params = useParams<{ id: string }>();
  const [experiment, setExperiment] = useState<ExperimentRecord | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  useEffect(() => {
    let cancelled = false;

    const timeoutId = setTimeout(() => {
      if (cancelled) return;

      const id = Number(params.id);
      if (!Number.isFinite(id)) {
        setLoadState("not-found");
        return;
      }

      setLoadState("loading");

      getHistoryEntry(id)
        .then((result) => {
          if (cancelled) return;
          if (result.kind === "ok") {
            setExperiment(result.data);
            setLoadState("ready");
          } else {
            // `client.ts`'s `ApiResult` doesn't distinguish 404 from other
            // non-2xx statuses (only 400/422/500 get dedicated variants) —
            // any failure here (including "experiment not found") surfaces
            // as the same generic error state.
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
  }, [params.id]);

  return (
    <section className="workspace">
      <header className="topbar">
        <div>
          <p className="eyebrow">Experiment History</p>
          <h2>Recorded experiment detail</h2>
        </div>
      </header>

      <div className="kb-content">
        <Link href="/history" className="history-detail-back">
          <ArrowLeft aria-hidden="true" size={14} />
          Back to History
        </Link>

        {loadState === "loading" && (
          <p className="kb-empty" aria-live="polite">
            Loading experiment…
          </p>
        )}

        {(loadState === "not-found" || loadState === "error") && (
          <p className="kb-empty kb-empty--error" role="alert">
            {loadState === "not-found"
              ? "This experiment does not exist."
              : "Could not load this experiment. Make sure the backend is running."}
          </p>
        )}

        {loadState === "ready" && experiment && (
          <ExperimentDetail experiment={experiment} />
        )}
      </div>
    </section>
  );
}
