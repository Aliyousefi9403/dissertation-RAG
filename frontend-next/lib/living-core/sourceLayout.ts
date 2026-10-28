import * as THREE from "three";

/** Shared source-node placement math, used by `SourceNodes`, `SourceLinkPaths`. */

/** Where each source's evidence line anchors on the core side. Kept just
 * outside `NeuralPointCloud`'s outer layer so paths visibly originate at
 * the core rather than passing through it. */
export const CORE_ANCHOR_RADIUS = 0.7;

/** Resting orbit radius once a source node has "arrived". */
export const SOURCE_FORMATION_RADIUS = 1.85;

/** Starting radius before the "arriving" choreography beat eases nodes
 * inward into `SOURCE_FORMATION_RADIUS`. */
export const SOURCE_ARRIVAL_START_RADIUS = 2.6;

function orbitAngleAndElevation(
  index: number,
  total: number,
): { angle: number; elevation: number } {
  const angle = (index / Math.max(1, total)) * Math.PI * 2;
  const elevation = (index % 2 === 0 ? 1 : -1) * (0.22 + (index % 3) * 0.1);
  return { angle, elevation };
}

/** The angle a given source index sits at. */
export function getSourceOrbitAngle(index: number, total: number): number {
  return orbitAngleAndElevation(index, total).angle;
}

/** A source node's settled position, once fully arrived. */
export function getSourceFormationPosition(index: number, total: number): THREE.Vector3 {
  const { angle, elevation } = orbitAngleAndElevation(index, total);
  return new THREE.Vector3(
    Math.cos(angle) * SOURCE_FORMATION_RADIUS,
    elevation,
    Math.sin(angle) * SOURCE_FORMATION_RADIUS,
  );
}

/** A source node's starting position at the beginning of the "arriving"
 * beat — further out and slightly more spread in elevation, so the motion
 * reads as nodes drawing inward into formation. */
export function getSourceArrivalStartPosition(index: number, total: number): THREE.Vector3 {
  const { angle, elevation } = orbitAngleAndElevation(index, total);
  return new THREE.Vector3(
    Math.cos(angle) * SOURCE_ARRIVAL_START_RADIUS,
    elevation * 1.4,
    Math.sin(angle) * SOURCE_ARRIVAL_START_RADIUS,
  );
}
