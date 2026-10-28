/** Backend `SourceItem.score` is the retriever's raw similarity score. */
const ASSUMED_SCORE_MIN = 0;
const ASSUMED_SCORE_MAX = 1;

/**
 * Normalises a raw similarity score to a `[0, 1]` visual intensity.
 */
export function scoreToVisual(score: number): number {
  if (!Number.isFinite(score)) {
    return 0;
  }

  const clamped = Math.min(ASSUMED_SCORE_MAX, Math.max(ASSUMED_SCORE_MIN, score));

  const range = ASSUMED_SCORE_MAX - ASSUMED_SCORE_MIN;
  if (range === 0) {
    return 0;
  }

  return (clamped - ASSUMED_SCORE_MIN) / range;
}
