"use client";

interface EvidenceCheckToggleProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  /** Compare mode has no evidence-checked variant yet. */
  disabled?: boolean;
}

/** Opt-in switch for the experimental evidence check. */
export function EvidenceCheckToggle({ enabled, onChange, disabled }: EvidenceCheckToggleProps) {
  const active = enabled && !disabled;

  return (
    <button
      type="button"
      role="switch"
      aria-checked={active}
      disabled={disabled}
      data-active={active}
      className="evidence-check-toggle"
      title={
        disabled
          ? "Evidence check is available in Clean and PWWS Poisoned modes only"
          : "Check the draft's claims against the retrieved sources before showing it (experimental)"
      }
      onClick={() => onChange(!enabled)}
    >
      <span className="evidence-check-toggle-track" aria-hidden="true">
        <span className="evidence-check-toggle-thumb" />
      </span>
      Evidence check
    </button>
  );
}
