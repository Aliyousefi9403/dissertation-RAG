"use client";

export type ExperimentMode = "clean" | "poisoned" | "compare" | "defended";

interface ExperimentModeSelectorProps {
  mode: ExperimentMode;
  onChange: (mode: ExperimentMode) => void;
}

const MODES: Array<{ value: ExperimentMode; label: string; disabled?: boolean }> = [
  { value: "clean", label: "Clean" },
  { value: "poisoned", label: "PWWS Poisoned" },
  { value: "compare", label: "Compare" },
  { value: "defended", label: "Defended", disabled: true },
];

/**
 * Small experiment-state control for the Assistant workspace: switches
 * between the clean baseline, the PWWS-poisoned knowledge base, a
 * side-by-side comparison of both, and the not-yet-available defended
 * pipeline. Purely a mode switch — it never calls the backend itself;
 * `app/page.tsx` reads `mode` to decide which endpoint the next submitted
 * question hits (`POST /chat` with `system_state`, or `POST /compare`).
 * "Defended" is rendered disabled and never becomes selectable, so no
 * defended-mode API call path exists to accidentally trigger.
 */
export function ExperimentModeSelector({
  mode,
  onChange,
}: ExperimentModeSelectorProps) {
  return (
    <div className="experiment-mode">
      <div
        className="experiment-mode-row"
        role="radiogroup"
        aria-label="Experiment state"
      >
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
            {option.disabled && (
              <span className="experiment-mode-badge">Coming soon</span>
            )}
          </button>
        ))}
      </div>

      {mode === "clean" && (
        <p
          className="experiment-mode-caption experiment-mode-caption--clean"
          role="status"
        >
          Clean baseline
        </p>
      )}

      {mode === "poisoned" && (
        <p
          className="experiment-mode-caption experiment-mode-caption--poisoned"
          role="status"
        >
          PWWS poisoned
        </p>
      )}
    </div>
  );
}
