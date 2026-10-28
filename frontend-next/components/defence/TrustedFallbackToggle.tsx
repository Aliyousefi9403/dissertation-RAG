"use client";

/** Verified mode only: when a refusal cannot be fixed, add the trusted MITRE entry as a source. */
export function TrustedFallbackToggle({
  enabled,
  onChange,
}: {
  enabled: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      data-active={enabled}
      className="evidence-check-toggle trusted-fallback-toggle"
      title="When the monitor cannot fix a refusal, answer from the trusted MITRE reference (upper bound)"
      onClick={() => onChange(!enabled)}
    >
      <span className="evidence-check-toggle-track" aria-hidden="true">
        <span className="evidence-check-toggle-thumb" />
      </span>
      Trusted fallback
    </button>
  );
}
