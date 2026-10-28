"use client";

import { useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

import {
  buildParticleConnections,
  buildParticleFieldLayout,
} from "@/lib/living-core/particleFieldLayout";
import { CURL_3D_GLSL, PERLIN_NOISE_3D_GLSL } from "@/components/living-core/gpu-particles/noiseGLSL";
import { LIVE_POSITION_GLSL } from "@/components/living-core/gpu-particles/intelligentCloudGLSL";
import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";
import { damp } from "@/lib/living-core/damp";

interface IntelligentParticleFieldProps {
  particleCount: number;
  phase: LivingCorePhase;
  /** True while PWWS Poisoned mode is the selected experiment state (see
   * `app/page.tsx`'s `experimentMode`). Overrides the phase-driven edge/
   * line color to `accent.danger`, fulfilling the `TODO(attack-detected)`
   * below — color only, no change to motion/shape/particle count. */
  attackDetected?: boolean;
  /** True while Compare mode is selected. Splits the point cloud ~50/50
   * into a red group (which also gets a small local orbit, see
   * `LIVE_POSITION_GLSL`) and a blue group holding the normal idle look —
   * mutually exclusive with `attackDetected` in practice (experiment mode
   * is a single selection), but independent uniforms either way. */
  compareMode?: boolean;
  /** Edge colour of the selected defence mode; null keeps the normal blue. */
  tint?: string | null;
}

// Constant idle-breathing/turbulence tuning -- always active regardless of
// phase, the baseline "waiting for input" look.
const CURL_AMP = 0.16;
const CURL_SCALE = 1.7;
const CURL_SPEED = 0.09;
const ATTRACT = 0.42;
const BREATHE_AMP = 0.045;
const BREATHE_FREQ = 0.32;

// The one phase-driven behavior this field has: while a question is in
// flight, the whole cloud contracts and expands together -- a much larger,
// synchronized pulse layered on top of the constant idle breathe above (see
// `LIVE_POSITION_GLSL`). `DIGEST_LAMBDA` eases `uDigestAmp` in/out instead
// of snapping it, matching this codebase's established damped-transition
// language (`lib/living-core/damp.ts`, used the same way by the retired
// `NeuralPointCloud`/still-live `RetrievalScan`).
const DIGEST_AMP_TARGET = 0.26;
const DIGEST_FREQ = 1.4;
const DIGEST_LAMBDA = 2.5;

// Color-ramp response rate (~400ms to settle, matching the product brief's
// "ramps up over 400ms" for the retrieving transition) and the resolved-
// state gold pulse's linear decay window before it settles back to the
// base blue target.
const COLOR_RAMP_LAMBDA = 7.5;
const RESOLVED_PULSE_DURATION = 0.8;

// Kept deliberately modest: with 15k-30k particles rendered additively,
// opacity/size stack fast under overlap. These values were tuned against a
// real screenshot (not guessed) so the cloud reads as a structured field of
// discrete points with visible curl-noise motion and connection lines
// rather than blowing bloom out into one undifferentiated white orb.
const POINT_OPACITY = 0.42;
const POINT_SIZE_BASE = 2.3;
const POINT_SIZE_MAX = 6.0;

// Core stays a fixed near-white highlight in every phase; only the edge/
// line color shifts with state (see the phase-driven target colors below --
// state color modulation is an explicitly approved exception to this
// field's otherwise-untouched physics/math).
const CORE_COLOR = new THREE.Color("#eaf6ff");
const EDGE_COLOR = new THREE.Color("#4a9fff");
const LINE_COLOR = new THREE.Color("#4a9fff");

// Phase-driven edge/line color targets (design tokens, lib/design-tokens.ts
// colors.accent.*). `IDLE_EDGE_TARGET` is also the resting color every other
// non-listed phase (dormant/unresolved/fault) settles to.
const IDLE_EDGE_TARGET = new THREE.Color("#4a9fff");
const RETRIEVING_EDGE_TARGET = new THREE.Color("#00e5ff");
const RESOLVED_PULSE_TARGET = new THREE.Color("#ffb84a");
// PWWS Poisoned mode's attack-detected target -- accent.danger
// (lib/design-tokens.ts), the same muted-red family `LivingCorePhase.fault`
// uses elsewhere in the Living Core system. Takes priority over every
// phase-driven target below while `attackDetected` is true.
const ATTACK_EDGE_TARGET = new THREE.Color("#FF4A6B");

// Compare mode's per-point red/blue split (POINTS_FRAGMENT only — the
// connection lines stay their normal uniform color). Reuses the same two
// established tokens as everywhere else in this file: accent.danger for
// red, the standing idle blue for blue — no new colors introduced.
const COMPARE_RED_COLOR = new THREE.Color("#FF4A6B");
const COMPARE_BLUE_COLOR = new THREE.Color("#4a9fff");

// Scratch instance reused every frame to avoid allocating a THREE.Color per
// frame just to compute the blended pulse target.
const scratchTargetColor = new THREE.Color();

const POINTS_VERTEX = /* glsl */ `
  attribute float aSeed;

  uniform float uSizeBase;
  uniform float uPixelRatio;

  varying float vSeed;

  // Calibrated against this scene's actual camera distance (see
  // CAMERA_BASE_POSITION in LivingCoreScene.tsx) -- a point at that
  // distance renders at uSizeBase device pixels, nearer/farther points
  // scale proportionally.
  const float REF_DISTANCE = 4.8;

  ${PERLIN_NOISE_3D_GLSL}
  ${CURL_3D_GLSL}
  ${LIVE_POSITION_GLSL}

  void main() {
    vSeed = aSeed;
    vec3 finalPosition = livePosition(position, aSeed);
    vec4 mvPosition = modelViewMatrix * vec4(finalPosition, 1.0);
    float perspectiveScale = REF_DISTANCE / max(0.001, -mvPosition.z);
    gl_PointSize = clamp(uSizeBase * perspectiveScale * uPixelRatio, 1.0, ${POINT_SIZE_MAX.toFixed(1)});
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const POINTS_FRAGMENT = /* glsl */ `
  uniform vec3 uColorCore;
  uniform vec3 uColorEdge;
  uniform float uOpacity;
  // Compare mode only -- same seed-based ~50/50 split formula as
  // LIVE_POSITION_GLSL's orbit branch, so a point's color and its motion
  // (orbiting or not) always agree.
  uniform float uCompareMode;
  uniform vec3 uColorRed;
  uniform vec3 uColorBlue;

  varying float vSeed;

  void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) {
      discard;
    }
    float falloff = smoothstep(0.5, 0.0, dist);
    float mixAmt = clamp(fract(vSeed * 7.0) * 0.6 + 0.15, 0.0, 1.0);
    vec3 color = mix(uColorEdge, uColorCore, mixAmt);

    if (uCompareMode > 0.5) {
      float isRedGroup = step(0.5, fract(vSeed * 13.7));
      vec3 splitColor = mix(uColorBlue, uColorRed, isRedGroup);
      color = mix(splitColor, uColorCore, mixAmt * 0.35);
    }
    gl_FragColor = vec4(color, uOpacity * falloff);
  }
`;

const LINES_VERTEX = /* glsl */ `
  attribute float aSeed;
  attribute vec3 aOtherPosition;
  attribute float aOtherSeed;

  varying float vDistance;

  ${PERLIN_NOISE_3D_GLSL}
  ${CURL_3D_GLSL}
  ${LIVE_POSITION_GLSL}

  void main() {
    vec3 selfLive = livePosition(position, aSeed);
    vec3 otherLive = livePosition(aOtherPosition, aOtherSeed);
    vDistance = length(selfLive - otherLive);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(selfLive, 1.0);
  }
`;

const LINES_FRAGMENT = /* glsl */ `
  uniform vec3 uColor;
  uniform float uMaxDistance;
  uniform float uOpacity;

  varying float vDistance;

  void main() {
    float fade = 1.0 - smoothstep(0.0, uMaxDistance, vDistance);
    gl_FragColor = vec4(uColor, fade * fade * uOpacity);
  }
`;

/**
 * The living core's centerpiece: a real GPU-simulated particle field, an
 * "intelligent cloud waiting for input" -- not a static shield, not a
 * particle sphere with no internal structure. Every particle's on-screen
 * position is recomputed from scratch each frame, entirely on the GPU
 * (`livePosition` in `intelligentCloudGLSL.ts`, shared verbatim between
 * this field's points and its connection-line geometry): divergence-free
 * curl-noise turbulence layered on a constant slow breathing pulse, gently
 * pulled back toward each particle's own rest radius so the cloud reads as
 * one coherent bounded body rather than dispersing. No CPU-side per-frame
 * work at all -- `useFrame` below only advances a single `uTime` uniform
 * on each material.
 *
 * The curl-noise/breathing/attraction motion baseline above is phase-
 * agnostic -- the same "waiting for input" look in every phase; the one
 * motion exception is `phase === "submitting"`, which ramps in a
 * synchronized open/close "digest" pulse (`uDigestAmp`, see
 * `LIVE_POSITION_GLSL`) in place of the old spinning radar sweep. Color IS
 * phase-driven: the edge/line color eases toward cyan while submitting and
 * briefly pulses gold on a fresh "converged" before settling back to the
 * base blue (see the target-color constants and the color-lerp block in
 * `useFrame` above). Further phase-driven behavior (convergence into a
 * shield form, ...) is still future work -- see the living-core-states doc.
 */
export function IntelligentParticleField({
  particleCount,
  phase,
  attackDetected = false,
  compareMode = false,
  tint = null,
}: IntelligentParticleFieldProps) {
  const tintColor = useMemo(() => (tint ? new THREE.Color(tint) : null), [tint]);
  const { gl } = useThree();
  const pointsMaterialRef = useRef<THREE.ShaderMaterial>(null);
  const linesMaterialRef = useRef<THREE.ShaderMaterial>(null);
  const digestAmpRef = useRef(0);
  const convergedEnteredAtRef = useRef<number | null>(null);
  const previousPhaseRef = useRef<LivingCorePhase>(phase);

  const layout = useMemo(() => buildParticleFieldLayout(particleCount), [particleCount]);
  const connections = useMemo(() => buildParticleConnections(layout), [layout]);

  const pointsGeometry = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(layout.positions, 3));
    geometry.setAttribute("aSeed", new THREE.Float32BufferAttribute(layout.seeds, 1));
    return geometry;
  }, [layout]);

  const linesGeometry = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(connections.positions, 3));
    geometry.setAttribute("aSeed", new THREE.Float32BufferAttribute(connections.seeds, 1));
    geometry.setAttribute(
      "aOtherPosition",
      new THREE.Float32BufferAttribute(connections.otherPositions, 3),
    );
    geometry.setAttribute("aOtherSeed", new THREE.Float32BufferAttribute(connections.otherSeeds, 1));
    return geometry;
  }, [connections]);

  // `useMemo` so the same object identity is passed to `<shaderMaterial
  // uniforms={...}>` across renders (three only reads this once at
  // construction); every per-frame *write* goes through the material ref
  // instead, per r3f's standard escape hatch for mutating a `useMemo`
  // result under the `react-hooks/immutability` lint rule.
  const pointsUniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uCurlAmp: { value: CURL_AMP },
      uCurlScale: { value: CURL_SCALE },
      uCurlSpeed: { value: CURL_SPEED },
      uAttract: { value: ATTRACT },
      uBreatheAmp: { value: BREATHE_AMP },
      uBreatheFreq: { value: BREATHE_FREQ },
      uDigestAmp: { value: 0 },
      uDigestFreq: { value: DIGEST_FREQ },
      uSizeBase: { value: POINT_SIZE_BASE },
      uPixelRatio: { value: gl.getPixelRatio() },
      uColorCore: { value: CORE_COLOR },
      uColorEdge: { value: EDGE_COLOR },
      uOpacity: { value: POINT_OPACITY },
      uCompareMode: { value: 0 },
      uColorRed: { value: COMPARE_RED_COLOR },
      uColorBlue: { value: COMPARE_BLUE_COLOR },
    }),
    [gl],
  );

  const linesUniforms = useMemo(
    () => ({
      uCurlAmp: { value: CURL_AMP },
      uCurlScale: { value: CURL_SCALE },
      uCurlSpeed: { value: CURL_SPEED },
      uAttract: { value: ATTRACT },
      uBreatheAmp: { value: BREATHE_AMP },
      uBreatheFreq: { value: BREATHE_FREQ },
      uDigestAmp: { value: 0 },
      uDigestFreq: { value: DIGEST_FREQ },
      uTime: { value: 0 },
      uColor: { value: LINE_COLOR },
      uMaxDistance: { value: connections.maxDistance },
      uOpacity: { value: 0.38 },
      uCompareMode: { value: 0 },
    }),
    [connections.maxDistance],
  );
  type PointsUniforms = typeof pointsUniforms;
  type LinesUniforms = typeof linesUniforms;

  useFrame(({ clock }, delta) => {
    const elapsed = clock.getElapsedTime();

    const targetDigestAmp = phase === "submitting" ? DIGEST_AMP_TARGET : 0;
    const dt = Math.min(0.1, Math.max(0, delta));
    digestAmpRef.current = damp(digestAmpRef.current, targetDigestAmp, DIGEST_LAMBDA, dt);

    // State color modulation: track the moment `phase` first becomes
    // "converged" so the resolved gold pulse always restarts at full
    // strength on a fresh convergence, then decays back to the base blue
    // target over `RESOLVED_PULSE_DURATION` regardless of how long the
    // field stays converged afterward.
    if (phase === "converged" && previousPhaseRef.current !== "converged") {
      convergedEnteredAtRef.current = elapsed;
    } else if (phase !== "converged") {
      convergedEnteredAtRef.current = null;
    }
    previousPhaseRef.current = phase;

    let targetEdgeColor = IDLE_EDGE_TARGET;
    if (attackDetected) {
      targetEdgeColor = ATTACK_EDGE_TARGET;
    } else if (tintColor) {
      targetEdgeColor = tintColor;
    } else if (phase === "submitting") {
      targetEdgeColor = RETRIEVING_EDGE_TARGET;
    } else if (phase === "converged" && convergedEnteredAtRef.current !== null) {
      const sinceConverged = elapsed - convergedEnteredAtRef.current;
      const pulseAmount = THREE.MathUtils.clamp(1 - sinceConverged / RESOLVED_PULSE_DURATION, 0, 1);
      targetEdgeColor = scratchTargetColor
        .copy(IDLE_EDGE_TARGET)
        .lerp(RESOLVED_PULSE_TARGET, pulseAmount);
    }
    const colorLerpAlpha = 1 - Math.exp(-COLOR_RAMP_LAMBDA * dt);

    const pointsMaterial = pointsMaterialRef.current;
    if (pointsMaterial) {
      const uniforms = pointsMaterial.uniforms as PointsUniforms;
      uniforms.uTime.value = elapsed;
      uniforms.uDigestAmp.value = digestAmpRef.current;
      uniforms.uColorEdge.value.lerp(targetEdgeColor, colorLerpAlpha);
      uniforms.uCompareMode.value = compareMode ? 1 : 0;
    }
    const linesMaterial = linesMaterialRef.current;
    if (linesMaterial) {
      const uniforms = linesMaterial.uniforms as LinesUniforms;
      uniforms.uTime.value = elapsed;
      uniforms.uDigestAmp.value = digestAmpRef.current;
      uniforms.uColor.value.lerp(targetEdgeColor, colorLerpAlpha);
      uniforms.uCompareMode.value = compareMode ? 1 : 0;
    }
  });

  return (
    <>
      <lineSegments geometry={linesGeometry} frustumCulled={false} renderOrder={0}>
        <shaderMaterial
          ref={linesMaterialRef}
          uniforms={linesUniforms}
          vertexShader={LINES_VERTEX}
          fragmentShader={LINES_FRAGMENT}
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </lineSegments>
      <points geometry={pointsGeometry} frustumCulled={false} renderOrder={1}>
        <shaderMaterial
          ref={pointsMaterialRef}
          uniforms={pointsUniforms}
          vertexShader={POINTS_VERTEX}
          fragmentShader={POINTS_FRAGMENT}
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </>
  );
}
