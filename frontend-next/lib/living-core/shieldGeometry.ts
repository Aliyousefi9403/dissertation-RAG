import * as THREE from "three";

/**
 * Single source of truth for the Aegis shield silhouette: a normalized "heater shield"
 * outline.
 */
export interface ShieldOutlinePoint {
  x: number;
  y: number;
}

interface ShieldBezierSegment {
  cp1: ShieldOutlinePoint;
  cp2: ShieldOutlinePoint;
  end: ShieldOutlinePoint;
}

// The top edge is a flat, (near-)straight line between two corners rather
// than a single rounded/pointed apex — a straight (or slightly peaked) top
// is what reads as "heraldic shield" instead of "leaf/teardrop."
const TOP_RIGHT: ShieldOutlinePoint = { x: 0.56, y: 0.94 };

/** The single point the whole silhouette tapers to. Also used as the
 * "composer-facing edge" anchor for the submitting-phase inbound pulse in
 * `ShieldShell`. */
export const SHIELD_BASE_POINT: ShieldOutlinePoint = { x: 0, y: -1 };

// Right-half descent: top-right corner -> shoulder -> waist -> bottom point.
const RIGHT_SHOULDER: ShieldOutlinePoint = { x: 0.74, y: 0.5 };
const RIGHT_WAIST: ShieldOutlinePoint = { x: 0.46, y: -0.28 };

// Flat top edge: every point (start, both control points, end) shares the
// same y, so this bezier renders as a straight horizontal line.
const SEGMENT_TOP_LEFT_TO_TOP_RIGHT: ShieldBezierSegment = {
  cp1: { x: -0.19, y: TOP_RIGHT.y },
  cp2: { x: 0.19, y: TOP_RIGHT.y },
  end: TOP_RIGHT,
};

const SEGMENT_TOP_RIGHT_TO_SHOULDER: ShieldBezierSegment = {
  cp1: { x: 0.72, y: 0.86 },
  cp2: { x: 0.76, y: 0.68 },
  end: RIGHT_SHOULDER,
};

const SEGMENT_SHOULDER_TO_WAIST: ShieldBezierSegment = {
  cp1: { x: 0.78, y: 0.28 },
  cp2: { x: 0.64, y: -0.02 },
  end: RIGHT_WAIST,
};

const SEGMENT_WAIST_TO_BASE: ShieldBezierSegment = {
  cp1: { x: 0.36, y: -0.56 },
  cp2: { x: 0.16, y: -0.82 },
  end: SHIELD_BASE_POINT,
};

function mirrorPoint(point: ShieldOutlinePoint): ShieldOutlinePoint {
  return { x: -point.x, y: point.y };
}

// The left-half ascent (base point -> left waist -> left shoulder ->
// top-left corner) is each right-half segment mirrored and walked in
// reverse: reversing a cubic bezier swaps its two control points.
const SEGMENT_BASE_TO_LEFT_WAIST: ShieldBezierSegment = {
  cp1: mirrorPoint(SEGMENT_WAIST_TO_BASE.cp2),
  cp2: mirrorPoint(SEGMENT_WAIST_TO_BASE.cp1),
  end: mirrorPoint(RIGHT_WAIST),
};

const SEGMENT_LEFT_WAIST_TO_SHOULDER: ShieldBezierSegment = {
  cp1: mirrorPoint(SEGMENT_SHOULDER_TO_WAIST.cp2),
  cp2: mirrorPoint(SEGMENT_SHOULDER_TO_WAIST.cp1),
  end: mirrorPoint(RIGHT_SHOULDER),
};

const SEGMENT_LEFT_SHOULDER_TO_TOP_LEFT: ShieldBezierSegment = {
  cp1: mirrorPoint(SEGMENT_TOP_RIGHT_TO_SHOULDER.cp2),
  cp2: mirrorPoint(SEGMENT_TOP_RIGHT_TO_SHOULDER.cp1),
  end: mirrorPoint(TOP_RIGHT),
};

const SHIELD_START_POINT: ShieldOutlinePoint = mirrorPoint(TOP_RIGHT);

/** Full closed-loop outline, starting and ending at the top-left corner
 * (`SHIELD_START_POINT`). */
const SHIELD_OUTLINE_SEGMENTS: ShieldBezierSegment[] = [
  SEGMENT_TOP_LEFT_TO_TOP_RIGHT,
  SEGMENT_TOP_RIGHT_TO_SHOULDER,
  SEGMENT_SHOULDER_TO_WAIST,
  SEGMENT_WAIST_TO_BASE,
  SEGMENT_BASE_TO_LEFT_WAIST,
  SEGMENT_LEFT_WAIST_TO_SHOULDER,
  SEGMENT_LEFT_SHOULDER_TO_TOP_LEFT,
];

/** Builds the flat 2D shield outline as a `THREE.Shape`, ready to extrude. */
export function createShieldShape(): THREE.Shape {
  const shape = new THREE.Shape();
  shape.moveTo(SHIELD_START_POINT.x, SHIELD_START_POINT.y);
  for (const segment of SHIELD_OUTLINE_SEGMENTS) {
    shape.bezierCurveTo(
      segment.cp1.x,
      segment.cp1.y,
      segment.cp2.x,
      segment.cp2.y,
      segment.end.x,
      segment.end.y,
    );
  }
  return shape;
}

export interface ShieldGeometryOptions {
  /** Scales the normalized -1..1 profile up to world units. */
  scale?: number;
  /** Extrusion thickness, in world units, along z. */
  depth?: number;
  /** Bevel size, in world units, softening the extruded edge. */
  bevelSize?: number;
}

/** A thin extruded shield mesh built directly from `createShieldShape`. */
export function createShieldGeometry({
  scale = 1,
  depth = 0.3,
  bevelSize = 0.05,
}: ShieldGeometryOptions = {}): THREE.ExtrudeGeometry {
  const shape = createShieldShape();
  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth,
    bevelEnabled: true,
    bevelThickness: bevelSize * 0.6,
    bevelSize,
    bevelSegments: 2,
    curveSegments: 14,
  });
  geometry.scale(scale, scale, 1);
  geometry.center();
  geometry.computeVertexNormals();
  return geometry;
}

/** Renders the same silhouette as an SVG `path` `d` attribute, for the pure DOM/CSS fallback. */
export function buildShieldSvgPath(viewBoxSize = 64, padding = 4): string {
  const usable = (viewBoxSize - padding * 2) / 2;
  const center = viewBoxSize / 2;

  const project = (point: ShieldOutlinePoint): string =>
    `${(center + point.x * usable).toFixed(2)},${(center - point.y * usable).toFixed(2)}`;

  const commands = SHIELD_OUTLINE_SEGMENTS.map(
    (segment) => `C ${project(segment.cp1)} ${project(segment.cp2)} ${project(segment.end)}`,
  );

  return `M ${project(SHIELD_START_POINT)} ${commands.join(" ")} Z`;
}
