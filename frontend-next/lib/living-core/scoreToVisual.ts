/**
 * Backend `SourceItem.score` is the retriever's raw similarity score (see
 * `lib/types/chat.ts`). Its numeric range is NOT documented or guaranteed by
 * the backend — it depends on whichever embedding model and distance metric
 * the retriever happens to use. This function therefore makes one explicit,
 * visual-only assumption: that typical scores fall within a
 * cosine-similarity-like `[0, 1]` band. That assumption exists purely to
 * pick a rendering intensity (instanced-node scale / color-mix) — it is
 * never surfaced as a calibrated "confidence" or "trust" figure, and never
 * relabelled as anything other than "similarity score" in the UI. Values
 * outside the assumed band are clamped, not treated as invalid.
 *
 * Moved unchanged from the retired `lib/shield-core/scoreToVisual.ts`.
 */
const ASSUMED_SCORE_MIN = 0;
const ASSUMED_SCORE_MAX = 1;

/**
 * Normalises a raw similarity score to a `[0, 1]` visual intensity.
 */
export function scoreToVisual(score: number): number {
  if (!Number.isFinite(score)) {
    return 0;
  }

  const clamped = Math.min(
    ASSUMED_SCORE_MAX,
    Math.max(ASSUMED_SCORE_MIN, score),
  );

  const range = ASSUMED_SCORE_MAX - ASSUMED_SCORE_MIN;
  if (range === 0) {
    return 0;
  }

  return (clamped - ASSUMED_SCORE_MIN) / range;
}
