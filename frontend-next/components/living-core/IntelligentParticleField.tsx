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

// Kept deliberately modest: with 15k-30k particles rendered additively,
// opacity/size stack fast under overlap. These values were tuned against a
// real screenshot (not guessed) so the cloud reads as a structured field of
// discrete points with visible curl-noise motion and connection lines
// rather than blowing bloom out into one undifferentiated white orb.
const POINT_OPACITY = 0.42;
const POINT_SIZE_BASE = 2.3;
const POINT_SIZE_MAX = 6.0;

// Blue/white only -- no other hue anywhere in this field.
const CORE_COLOR = new THREE.Color("#eaf6ff");
const EDGE_COLOR = new THREE.Color("#3aa0ff");
const LINE_COLOR = new THREE.Color("#5fb4ff");

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
 * Mostly phase-agnostic -- the curl-noise/breathing/attraction baseline
 * above is the same "waiting for input" look in every phase. The one
 * exception is `phase === "submitting"`, which ramps in a synchronized
 * open/close "digest" pulse (`uDigestAmp`, see `LIVE_POSITION_GLSL`) in
 * place of the old spinning radar sweep -- the core itself now communicates
 * "processing a question" rather than a separate UI element behind it.
 * Further phase-driven behavior (convergence into a shield form, ...) is
 * still future work -- see the living-core-states doc.
 */
export function IntelligentParticleField({ particleCount, phase }: IntelligentParticleFieldProps) {
  const { gl } = useThree();
  const pointsMaterialRef = useRef<THREE.ShaderMaterial>(null);
  const linesMaterialRef = useRef<THREE.ShaderMaterial>(null);
  const digestAmpRef = useRef(0);

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

    const pointsMaterial = pointsMaterialRef.current;
    if (pointsMaterial) {
      const uniforms = pointsMaterial.uniforms as PointsUniforms;
      uniforms.uTime.value = elapsed;
      uniforms.uDigestAmp.value = digestAmpRef.current;
    }
    const linesMaterial = linesMaterialRef.current;
    if (linesMaterial) {
      const uniforms = linesMaterial.uniforms as LinesUniforms;
      uniforms.uTime.value = elapsed;
      uniforms.uDigestAmp.value = digestAmpRef.current;
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
