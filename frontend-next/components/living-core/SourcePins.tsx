import type { SourceItem } from "@/lib/types/chat";

interface SourcePinsProps {
  sources: SourceItem[];
}

interface PinSpec {
  leftPercent: number;
  topPercent: number;
}

// Fixed positions per the product brief -- not derived from source content,
// so only the first 3 grounded sources ever get a pin.
const PIN_POSITIONS: PinSpec[] = [
  { leftPercent: 65, topPercent: 25 },
  { leftPercent: 30, topPercent: 65 },
  { leftPercent: 20, topPercent: 40 },
];

/** Floating numbered badges over the particle field, one per grounded source. */
export function SourcePins({ sources }: SourcePinsProps) {
  const pins = sources.slice(0, PIN_POSITIONS.length);

  if (pins.length === 0) {
    return null;
  }

  return (
    <div className="source-pins" aria-hidden="true">
      <svg className="source-pin-lines" viewBox="0 0 100 100" preserveAspectRatio="none">
        {pins.map((source, index) => {
          const { leftPercent, topPercent } = PIN_POSITIONS[index];
          const endY = 15 + index * 30;
          const controlX = (leftPercent + 100) / 2;
          return (
            <path
              key={source.source}
              className="source-pin-line"
              d={`M ${leftPercent} ${topPercent} Q ${controlX} ${topPercent} 100 ${endY}`}
              pathLength={1}
            />
          );
        })}
      </svg>
      {pins.map((source, index) => {
        const { leftPercent, topPercent } = PIN_POSITIONS[index];
        return (
          <div
            key={source.source}
            className="source-pin"
            style={{ left: `${leftPercent}%`, top: `${topPercent}%` }}
          >
            {source.source_number}
          </div>
        );
      })}
    </div>
  );
}
