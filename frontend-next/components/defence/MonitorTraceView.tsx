"use client";

import type { MonitorRound, MonitorTrace, MonitorViolation } from "@/lib/types/monitor";

const OUTCOME: Record<MonitorTrace["outcome"], { label: string; tone: string }> = {
  released: { label: "Verified and released", tone: "pass" },
  released_refusal: { label: "Released as a refusal: evidence missing", tone: "warn" },
  restored: { label: "Restored from the trusted MITRE reference", tone: "restore" },
  withheld: { label: "Withheld: unsupported terms could not be removed", tone: "fail" },
};

const RULES: Array<{ spec: MonitorViolation["spec"]; name: string; text: string }> = [
  {
    spec: "phi1_lexical",
    name: "φ₁ lexical conformance",
    text: "every rare word appears in the trusted MITRE vocabulary",
  },
  {
    spec: "phi2_availability",
    name: "φ₂ evidence availability",
    text: "no refusal when MITRE covers the attack",
  },
];

function RoundCard({ round }: { round: MonitorRound }) {
  const isRestore = round.round === "restore";
  return (
    <li className="monitor-round" data-restore={isRestore}>
      <p className="monitor-round-title">
        {isRestore
          ? `Trusted fallback · ${round.trusted_ids}`
          : `Attempt ${(round.round as number) + 1}`}
        {!isRestore && (round.skipped_quarantined ?? 0) > 0 && (
          <span className="monitor-round-skip">
            {" "}
            · {round.skipped_quarantined} quarantined{" "}
            {round.skipped_quarantined === 1 ? "passage" : "passages"} skipped
          </span>
        )}
      </p>
      <ul className="monitor-rules">
        {RULES.map((rule) => {
          const v = round.violations.find((x) => x.spec === rule.spec);
          return (
            <li key={rule.spec} className="monitor-rule" data-pass={!v}>
              <span className="monitor-rule-mark" aria-hidden="true">
                {v ? "✗" : "✓"}
              </span>
              <span>
                <strong>{rule.name}</strong> — {rule.text}
                {v && v.witnesses.length > 0 && (
                  <span className="monitor-witnesses">
                    {" "}
                    ·{" "}
                    {v.witnesses.map((w) => (
                      <code key={w}>{w}</code>
                    ))}
                  </span>
                )}
                <span className="sr-only">{v ? " violated" : " holds"}</span>
              </span>
            </li>
          );
        })}
      </ul>
      {(round.quarantined?.length ?? 0) > 0 && (
        <p className="monitor-quarantine-note">
          ⛔ {round.quarantined!.length} {round.quarantined!.length === 1 ? "passage" : "passages"}{" "}
          quarantined; feedback sent to the model
        </p>
      )}
    </li>
  );
}

/** Verified mode: the runtime monitor's real trace for this answer. */
export function MonitorTraceView({ trace }: { trace: MonitorTrace }) {
  const outcome = OUTCOME[trace.outcome];
  return (
    <section
      className="defence-view defence-view--monitor"
      aria-label="Runtime monitor"
      data-testid="monitor-trace"
    >
      <header className="defence-view-head">
        <span className="defence-view-icon" aria-hidden="true">
          ⌘
        </span>
        <div>
          <p className="eyebrow">
            Runtime monitor · {trace.policy_version}
            {trace.trusted_fallback ? " · trusted fallback on" : ""}
          </p>
          <h3 className="monitor-outcome" data-tone={outcome.tone} role="status">
            {outcome.label}
          </h3>
        </div>
      </header>
      <ol className="monitor-rounds">
        {trace.rounds.map((round, index) => (
          <RoundCard key={index} round={round} />
        ))}
      </ol>
      <p className="monitor-footnote">
        {trace.generations} {trace.generations === 1 ? "generation" : "generations"} · φ₃ memory
        safety: quarantined passages are never retrieved again
      </p>
    </section>
  );
}
