import type { EvidenceCheckResult, EvidenceClaim, EvidenceOutcome } from "@/lib/types/guardedChat";

const HEADLINES: Record<EvidenceOutcome, string> = {
  supported: "Claims are stated in the retrieved sources",
  unsupported: "Draft withheld — claims not found in the sources",
  contradicted: "Draft withheld — sources contradict the draft",
  unavailable: "Draft withheld — evidence check unavailable",
  abstained: "The answer declines — sources were insufficient",
};

const STATUS_LABELS: Record<EvidenceOutcome, string> = {
  supported: "Supported",
  unsupported: "Unsupported",
  contradicted: "Contradicted",
  unavailable: "Unavailable",
  abstained: "Abstained",
};

const FAILURE_STAGES: Record<string, string> = {
  retrieval: "Retrieval",
  generation: "Draft generation",
  verification: "Verification",
};

function ClaimRow({ claim }: { claim: EvidenceClaim }) {
  return (
    <li className="evidence-claim" data-status={claim.status}>
      <div className="evidence-claim-head">
        <span className="evidence-claim-status" data-status={claim.status}>
          {STATUS_LABELS[claim.status]}
        </span>
        {claim.source_ids.length > 0 && (
          <span className="evidence-claim-sources">{claim.source_ids.join(", ")}</span>
        )}
      </div>
      <p className="evidence-claim-text">{claim.claim}</p>
      {claim.explanation && <p className="evidence-claim-note">{claim.explanation}</p>}
      {claim.quotes.length > 0 && (
        <ul className="evidence-quotes">
          {claim.quotes.map((quote, index) => (
            <li key={`${quote.source_id}-${index}`} data-verified={quote.verified}>
              <span className="evidence-quote-source">{quote.source_id}</span>
              <q>{quote.text}</q>
              <span className="evidence-quote-check">
                {quote.verified ? "Found in source" : "Not found in source"}
              </span>
            </li>
          ))}
        </ul>
      )}
      {claim.problems.length > 0 && (
        <p className="evidence-claim-note evidence-claim-note--warn">{claim.problems.join("; ")}</p>
      )}
    </li>
  );
}

/**
 * Shows the actual outcome of the experimental evidence check for one
 * answer (`POST /guarded-chat`). Every value here comes from the backend
 * response — nothing is derived or invented client-side, and there is no
 * confidence percentage. "Supported" means the retrieved sources state the
 * claim; it is not proof the claim is true or that the sources are clean.
 */
export function EvidenceCheckCard({ result }: { result: EvidenceCheckResult }) {
  const withheld = result.decision === "withheld";

  return (
    <section
      className="evidence-check-card"
      data-outcome={result.outcome}
      role={withheld ? "alert" : "status"}
      aria-label="Evidence check result"
    >
      <p className="eyebrow">Evidence check · experimental</p>
      <strong className="evidence-check-headline">{HEADLINES[result.outcome]}</strong>
      <p className="evidence-check-explanation">{result.explanation}</p>

      {result.failures.length > 0 && (
        <ul className="evidence-check-failures">
          {result.failures.map((failure, index) => (
            <li key={`${failure.stage}-${index}`}>
              {FAILURE_STAGES[failure.stage] ?? failure.stage} failed
              {failure.timeout ? " (timed out)" : ` (${failure.type})`}
            </li>
          ))}
        </ul>
      )}

      {result.claims.length > 0 && (
        <details className="evidence-check-claims" open={withheld}>
          <summary>
            {result.claims.length} {result.claims.length === 1 ? "claim" : "claims"} checked
          </summary>
          <ul>
            {result.claims.map((claim, index) => (
              <ClaimRow key={index} claim={claim} />
            ))}
          </ul>
        </details>
      )}

      <p className="evidence-check-caveat">{result.label}</p>

      <p className="evidence-check-audit" data-saved={result.audit.saved}>
        {result.audit.saved
          ? `Audit record saved · run ${result.audit.run_id}`
          : `Audit record NOT saved — ${result.audit.error ?? "unknown error"}`}
        {" · "}
        {result.policy_version}
      </p>
    </section>
  );
}
