const BEAM_COUNT = 8;
const BEAM_ANGLES = Array.from({ length: BEAM_COUNT }, (_, index) => (360 / BEAM_COUNT) * index);

/** Faint radial "energy tendril" beams emanating from the living core's center. */
export function EnergyBeams() {
  return (
    <div className="energy-beams" aria-hidden="true">
      {BEAM_ANGLES.map((angle) => (
        <span
          key={angle}
          className="energy-beam"
          style={{ transform: `translate(-50%, -50%) rotate(${angle}deg)` }}
        />
      ))}
    </div>
  );
}
