"use client";

import { useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

import {
  buildParticleConnections,
  buildParticleFieldLayout,
} from "@/lib/living-core/particleFieldLayout";
import {
  CURL_3D_GLSL,
  PERLIN_NOISE_3D_GLSL,
} from "@/components/living-core/gpu-particles/noiseGLSL";
import { LIVE_POSITION_GLSL } from "@/components/living-core/gpu-particles/intelligentCloudGLSL";
import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";
import { damp } from "@/lib/living-core/damp";

interface IntelligentParticleFieldProps {
  particleCount: number;
  phase: LivingCorePhase;
  /** True while PWWS Poisoned mode is the selected experiment state. */
  attackDetected?: boolean;
  /** True while Compare mode is selected. */
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

// "Digest" wobble while a question is in flight.
const DIGEST_AMP_TARGET = 0.26;
const DIGEST_FREQ = 1.4;
const DIGEST_LAMBDA = 2.5;

// Colour easing rate, and how long the gold pulse lasts after an answer lands.
const COLOR_RAMP_LAMBDA = 7.5;
const RESOLVED_PULSE_DURATION = 0.8;

// Kept low: 15k-30k additive particles saturate quickly.
const POINT_OPACITY = 0.42;
const POINT_SIZE_BASE = 2.3;
const POINT_SIZE_MAX = 6.0;

// Core stays a fixed near-white highlight in every phase.
const CORE_COLOR = new THREE.Color("#eaf6ff");
const EDGE_COLOR = new THREE.Color("#4a9fff");
const LINE_COLOR = new THREE.Color("#4a9fff");

// Phase-driven edge/line color targets (design tokens, lib/design-tokens.ts
// colors.accent.*). `IDLE_EDGE_TARGET` is also the resting color every other
// non-listed phase (dormant/unresolved/fault) settles to.
const IDLE_EDGE_TARGET = new THREE.Color("#4a9fff");
const RETRIEVING_EDGE_TARGET = new THREE.Color("#00e5ff");
const RESOLVED_PULSE_TARGET = new THREE.Color("#ffb84a");
// PWWS Poisoned mode's attack-detected target.
const ATTACK_EDGE_TARGET = new THREE.Color("#FF4A6B");

// Compare mode's per-point red/blue split.
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

  // Calibrated against this scene's actual camera distance.
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

/** The living core's centerpiece: a real GPU-simulated particle field. */
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
    geometry.setAttribute(
      "aOtherSeed",
      new THREE.Float32BufferAttribute(connections.otherSeeds, 1),
    );
    return geometry;
  }, [connections]);

  // `useMemo` so the same object identity is passed to `<shaderMaterial uniforms={...}>` across
  // renders.
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

    // State color modulation: track the moment `phase` first becomes "converged" so the
    // resolved gold pulse always restarts at full strength on a fresh convergence, then decays
    // back to the base blue target over `RESOLVED_PULSE_DURATION` regardless of how long the
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
