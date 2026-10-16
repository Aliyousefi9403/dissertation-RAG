const BEAM_COUNT = 8;
const BEAM_ANGLES = Array.from({ length: BEAM_COUNT }, (_, index) => (360 / BEAM_COUNT) * index);

/**
 * Faint radial "energy tendril" beams emanating from the living core's
 * center -- pure DOM/CSS, no WebGL. A fixed fan of `BEAM_COUNT` thin
 * gradient lines that slowly rotates as one group (`.energy-beams`'
 * animation in globals.css), never fast enough to read as spinning.
 * Deliberately outside the r3f canvas: this is ambient set-dressing over
 * the particle field, not part of its rendering physics/math.
 */
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
