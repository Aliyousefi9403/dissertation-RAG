"use client";

import type { SourceItem } from "@/lib/types/chat";
import { fileName, verdictOf } from "@/components/defence/filterVerdict";

/**
 * Repaired mode: a tracked-changes ledger. For each passage the model read, the words the repair
 * policy replaced (struck through) and their likely originals, with the gap in bits and the
 * passage score before and after repair. Real response data only.
 */
export function RepairLedger({ sources }: { sources: SourceItem[] }) {
  const rows = sources
    .map((s) => ({ source: s, verdict: verdictOf(s) }))
    .filter((r) => r.verdict !== null);
  const total = rows.reduce((n, r) => n + (r.verdict!.repairs?.length ?? 0), 0);

  return (
    <section className="defence-view defence-view--repair" aria-label="Repair ledger" data-testid="repair-ledger">
      <header className="defence-view-head">
        <span className="defence-view-icon" aria-hidden="true">✎</span>
        <div>
          <p className="eyebrow">Repair ledger</p>
          <h3>
            {total === 0 ? "No words needed repair" : `${total} ${total === 1 ? "word" : "words"} restored before the model read them`}
          </h3>
        </div>
      </header>
      <ol className="repair-ledger-list">
        {rows.map(({ source, verdict }) => (
          <li key={source.source_number} className="repair-ledger-row">
            <div className="repair-ledger-meta">
              <span className="repair-ledger-file">[{source.source_number}] {fileName(source.source)}</span>
              {verdict!.score_before_repair_bits !== undefined && (
                <span className="repair-ledger-score">
                  {verdict!.score_before_repair_bits.toFixed(2)} → <strong>{verdict!.score_bits.toFixed(2)} bits</strong>
                  <span className="repair-ledger-threshold"> (threshold {verdict!.threshold_bits})</span>
                </span>
              )}
            </div>
            {(verdict!.repairs?.length ?? 0) === 0 ? (
              <p className="repair-ledger-none">Kept unchanged</p>
            ) : (
              <p className="repair-ledger-changes">
                {verdict!.repairs!.map((r) => (
                  <span key={r.word} className="repair-change" title={`gap ${r.gap_bits.toFixed(1)} bits`}>
                    <del>{r.word}</del>
                    <ins>{r.replacement}</ins>
                  </span>
                ))}
              </p>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
