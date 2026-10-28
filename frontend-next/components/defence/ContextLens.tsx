"use client";

import type { SourceItem } from "@/lib/types/chat";
import { skippedPassageCount } from "@/lib/living-core/defenceShield";
import { fileName, verdictOf } from "@/components/defence/filterVerdict";

/**
 * Contextual mode: a language-model lens over each passage the model read. A gauge shows the
 * passage's contextual synonym-gap score against the frozen threshold, and the words that fit
 * the sentence worst glow by their gap in bits, each with the word the language model prefers.
 */
export function ContextLens({ sources }: { sources: SourceItem[] }) {
  const rows = sources
    .map((s) => ({ source: s, verdict: verdictOf(s) }))
    .filter((r) => r.verdict !== null);
  const skipped = skippedPassageCount(sources);

  return (
    <section className="defence-view defence-view--context" aria-label="Context lens" data-testid="context-lens">
      <header className="defence-view-head">
        <span className="defence-view-icon" aria-hidden="true">◎</span>
        <div>
          <p className="eyebrow">Context lens · language model as reference</p>
          <h3>
            {skipped === null
              ? "Passages scored in context"
              : skipped === 0
                ? "Every passage fits its context"
                : `${skipped} ${skipped === 1 ? "passage" : "passages"} did not fit their context and were skipped`}
          </h3>
        </div>
      </header>
      <ul className="context-lens-list">
        {rows.map(({ source, verdict }) => {
          // The gauge spans 0 to twice the threshold, so the threshold mark sits at the middle.
          const ratio = Math.min(1, verdict!.score_bits / (verdict!.threshold_bits * 2));
          const mark = 0.5;
          return (
            <li key={source.source_number} className="context-lens-row">
              <div className="context-lens-meta">
                <span>[{source.source_number}] {fileName(source.source)}</span>
                <span>
                  <strong>{verdict!.score_bits.toFixed(2)}</strong> / {verdict!.threshold_bits} bits
                </span>
              </div>
              <div className="context-lens-gauge" role="img"
                   aria-label={`score ${verdict!.score_bits.toFixed(2)} bits, threshold ${verdict!.threshold_bits} bits`}>
                <span className="context-lens-fill" style={{ width: `${ratio * 100}%` }} />
                <span className="context-lens-mark" style={{ left: `${mark * 100}%` }} />
              </div>
              {(verdict!.top_words?.length ?? 0) > 0 && (
                <p className="context-lens-words">
                  {verdict!.top_words!.map((w) => (
                    <span key={w.word} className="context-word"
                          style={{ ["--heat" as string]: Math.min(1, Math.max(0.15, w.gap_bits / 12)) }}
                          title={`${w.gap_bits.toFixed(1)} bits less likely than "${w.likely_original}"`}>
                      {w.word}<span className="context-word-alt">→ {w.likely_original}</span>
                    </span>
                  ))}
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
