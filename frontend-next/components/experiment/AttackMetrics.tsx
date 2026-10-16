import type {
  CompareMetrics,
  AttackQualityMetrics,
  RetrievalQualityMetrics,
  GenerationQualityMetrics,
  AttackSuccessMetrics,
} from "@/lib/types/compare";

interface AttackMetricsProps {
  metrics: CompareMetrics;
  attackQuality?: AttackQualityMetrics | null;
  retrievalQuality?: RetrievalQualityMetrics | null;
  generationQuality?: GenerationQualityMetrics | null;
  attackSuccess?: AttackSuccessMetrics | null;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatScore(value: number): string {
  return value.toFixed(4);
}

function formatSignedScore(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(4)}`;
}

/** Renders a 0-1 ratio/score, or "N/A" when the backend could not
 * evaluate it (e.g. no ground-truth match for this question, or the LLM
 * judge call failed) -- distinct from a genuine 0.0 score. */
function formatMaybeScore(value: number | null | undefined): string {
  return value === null || value === undefined ? "N/A" : value.toFixed(4);
}

function formatMaybePercent(value: number | null | undefined): string {
  return value === null || value === undefined ? "N/A" : formatPercent(value);
}

function formatMaybeHit(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  return value === 1 ? "HIT" : "MISS";
}

function formatMaybeBool(value: boolean | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  return value ? "YES" : "NO";
}

/**
 * Renders `CompareResponse.metrics` verbatim — every value comes straight
 * from the backend `/compare` response. No severity, confidence, trust
 * score or attack-success figures are computed or invented here.
 *
 * The four optional groups (attack/retrieval/generation quality, attack
 * success) are additive research metrics layered on top of the original
 * grid below, grouped under their own `.eyebrow` label but reusing the
 * same `.attack-metrics-grid`/`.attack-metric` styling. Each group renders
 * only when the backend actually returned it (older History records and
 * pre-migration responses have these as `null`).
 */
export function AttackMetrics({
  metrics,
  attackQuality,
  retrievalQuality,
  generationQuality,
  attackSuccess,
}: AttackMetricsProps) {
  return (
    <section className="attack-metrics" aria-label="Attack impact">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Attack impact</p>
        </div>
      </div>

      <dl className="attack-metrics-grid">
        <div className="attack-metric">
          <dt>Attack method</dt>
          <dd>{metrics.attack_method.toUpperCase()}</dd>
        </div>

        <div className="attack-metric">
          <dt>Retrieval shift</dt>
          <dd>{formatPercent(metrics.retrieval_shift)}</dd>
        </div>

        <div className="attack-metric">
          <dt>Top-K overlap</dt>
          <dd>{formatPercent(metrics.top_k_overlap)}</dd>
        </div>

        <div className="attack-metric">
          <dt>Clean top score</dt>
          <dd>{formatScore(metrics.clean_top_score)}</dd>
        </div>

        <div className="attack-metric">
          <dt>Poisoned top score</dt>
          <dd>{formatScore(metrics.poisoned_top_score)}</dd>
        </div>

        <div className="attack-metric">
          <dt>Top score delta</dt>
          <dd>{formatSignedScore(metrics.top_score_delta)}</dd>
        </div>

        <div className="attack-metric">
          <dt>Shared chunks</dt>
          <dd>
            {metrics.shared_chunks} / {metrics.top_k}
          </dd>
        </div>

        <div className="attack-metric">
          <dt>Answer changed</dt>
          <dd>{metrics.answer_changed ? "YES" : "NO"}</dd>
        </div>
      </dl>

      {attackQuality && (
        <>
          <p className="eyebrow research-metric-group-label">Attack quality</p>
          <dl className="attack-metrics-grid">
            <div className="attack-metric">
              <dt>Semantic similarity</dt>
              <dd>{formatMaybeScore(attackQuality.mean_semantic_similarity)}</dd>
            </div>
            <div className="attack-metric">
              <dt>Modification rate</dt>
              <dd>{formatMaybePercent(attackQuality.mean_modification_rate)}</dd>
            </div>
          </dl>
        </>
      )}

      {retrievalQuality && (
        <>
          <p className="eyebrow research-metric-group-label">Retrieval</p>
          <dl className="attack-metrics-grid">
            <div className="attack-metric">
              <dt>Poison Hit@3</dt>
              <dd>{formatMaybeHit(retrievalQuality.poison_hit_at_3)}</dd>
            </div>
            <div className="attack-metric">
              <dt>Clean Hit@3</dt>
              <dd>{formatMaybeHit(retrievalQuality.clean_hit_at_3)}</dd>
            </div>
            <div className="attack-metric">
              <dt>Poisoned Hit@3</dt>
              <dd>{formatMaybeHit(retrievalQuality.poisoned_hit_at_3)}</dd>
            </div>
            <div className="attack-metric">
              <dt>Clean RR</dt>
              <dd>{formatMaybeScore(retrievalQuality.clean_reciprocal_rank)}</dd>
            </div>
            <div className="attack-metric">
              <dt>Poisoned RR</dt>
              <dd>{formatMaybeScore(retrievalQuality.poisoned_reciprocal_rank)}</dd>
            </div>
          </dl>
        </>
      )}

      {generationQuality && (
        <>
          <p className="eyebrow research-metric-group-label">Answer quality</p>
          <dl className="attack-metrics-grid">
            <div className="attack-metric">
              <dt>Clean correctness</dt>
              <dd>{formatMaybeScore(generationQuality.clean_answer_correctness)}</dd>
            </div>
            <div className="attack-metric">
              <dt>Poisoned correctness</dt>
              <dd>{formatMaybeScore(generationQuality.poisoned_answer_correctness)}</dd>
            </div>
            <div className="attack-metric">
              <dt>Clean faithfulness</dt>
              <dd>{formatMaybeScore(generationQuality.clean_faithfulness)}</dd>
            </div>
            <div className="attack-metric">
              <dt>Poisoned faithfulness</dt>
              <dd>{formatMaybeScore(generationQuality.poisoned_faithfulness)}</dd>
            </div>
          </dl>
        </>
      )}

      {attackSuccess && (
        <>
          <p className="eyebrow research-metric-group-label">Overall</p>
          <dl className="attack-metrics-grid">
            <div className="attack-metric">
              <dt>RAG attack successful</dt>
              <dd>{formatMaybeBool(attackSuccess.rag_attack_success)}</dd>
            </div>
          </dl>
        </>
      )}
    </section>
  );
}
