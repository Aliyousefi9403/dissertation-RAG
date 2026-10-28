"use client";

export type ExperimentMode =
  | "clean"
  | "poisoned"
  | "compare"
  | "defended"
  | "repaired"
  | "contextual"
  | "verified";

interface ExperimentModeSelectorProps {
  mode: ExperimentMode;
  onChange: (mode: ExperimentMode) => void;
}

const MODES: Array<{ value: ExperimentMode; label: string; disabled?: boolean }> = [
  { value: "clean", label: "Clean" },
  { value: "poisoned", label: "PWWS Poisoned" },
  { value: "compare", label: "Compare" },
  { value: "defended", label: "Defended" },
  { value: "repaired", label: "Repaired" },
  { value: "contextual", label: "Contextual" },
  { value: "verified", label: "Verified" },
];

/** Experiment-mode switch for the Assistant workspace. */
export function ExperimentModeSelector({ mode, onChange }: ExperimentModeSelectorProps) {
  return (
    <div className="experiment-mode">
      <div className="experiment-mode-row" role="radiogroup" aria-label="Experiment state">
        {MODES.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={mode === option.value}
            disabled={option.disabled}
            data-active={mode === option.value}
            data-mode={option.value}
            className="experiment-mode-button"
            onClick={() => onChange(option.value)}
          >
            {option.label}
            {option.disabled && <span className="experiment-mode-badge">Coming soon</span>}
          </button>
        ))}
      </div>

      {mode === "clean" && (
        <p className="experiment-mode-caption experiment-mode-caption--clean" role="status">
          Clean baseline
        </p>
      )}

      {mode === "defended" && (
        <p className="experiment-mode-caption experiment-mode-caption--defended" role="status">
          PWWS poisoned + entropy filter
        </p>
      )}

      {mode === "repaired" && (
        <p className="experiment-mode-caption experiment-mode-caption--repaired" role="status">
          PWWS poisoned + entropy repair
        </p>
      )}

      {mode === "contextual" && (
        <p className="experiment-mode-caption experiment-mode-caption--contextual" role="status">
          PWWS poisoned + language-model filter
        </p>
      )}

      {mode === "verified" && (
        <p className="experiment-mode-caption experiment-mode-caption--verified" role="status">
          PWWS poisoned + runtime verification monitor
        </p>
      )}

      {mode === "poisoned" && (
        <p className="experiment-mode-caption experiment-mode-caption--poisoned" role="status">
          PWWS poisoned
        </p>
      )}
    </div>
  );
}
