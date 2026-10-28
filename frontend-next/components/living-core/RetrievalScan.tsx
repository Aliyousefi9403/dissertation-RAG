"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";
import { LIVING_CORE_PHASE_COLOR } from "@/lib/living-core/livingCorePalette";
import { getSourceOrbitAngle } from "@/lib/living-core/sourceLayout";
import { damp } from "@/lib/living-core/damp";
import type { SourceItem } from "@/lib/types/chat";

interface RetrievalScanProps {
  phase: LivingCorePhase;
  /** Real sources only — the caller (`LivingCoreScene`) passes `[]` for
   * every phase except "converged", exactly like `SourceNodes`/
   * `SourceLinkPaths`. This component never invents a marker count. */
  sources: SourceItem[];
}

const PLANE_RADIUS = 1.35;
const MARKER_RADIUS = PLANE_RADIUS * 0.72;

interface ScanTargets {
  opacity: number;
  sweepSpeed: number;
}

/** Scan strength and speed for each phase. */
function computeScanTargets(phase: LivingCorePhase): ScanTargets {
  switch (phase) {
    case "dormant":
      return { opacity: 0, sweepSpeed: 0 };
    case "idle":
      return { opacity: 0.06, sweepSpeed: 0.05 };
    case "submitting":
      // No spinning sweep while a question is in flight — the particle
      // core itself communicates "processing" now, via its own digest-pulse
      // open/close motion (see `IntelligentParticleField`'s `uDigestAmp`).
      return { opacity: 0, sweepSpeed: 0 };
    case "converged":
      return { opacity: 0.32, sweepSpeed: 0.3 };
    case "unresolved":
      return { opacity: 0.12, sweepSpeed: 0.08 };
    case "fault":
      return { opacity: 0.15, sweepSpeed: 0 };
    default: {
      const exhaustiveCheck: never = phase;
      return exhaustiveCheck;
    }
  }
}

const VERTEX_SHADER = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

/**
 * Ring-pulse + radial-spoke + sweep-beam math ported from react-bits' `Radar/Radar.tsx` donor
 * into this project's existing `THREE.ShaderMaterial`.
 */
const FRAGMENT_SHADER = /* glsl */ `
  uniform float uTime;
  uniform float uSweepSpeed;
  uniform float uOpacity;
  uniform vec3 uColor;

  varying vec2 vUv;

  const float TAU = 6.28318530718;
  const float RING_COUNT = 5.0;
  const float RING_THICKNESS = 0.045;
  const float SPOKE_COUNT = 8.0;
  const float SPOKE_THICKNESS = 0.012;
  const float SWEEP_WIDTH = 2.4;

  void main() {
    vec2 centered = (vUv - vec2(0.5)) * 2.0;
    float radius = length(centered);
    if (radius > 1.0) {
      discard;
    }

    float angle = atan(centered.y, centered.x);

    // Concentric rings pulsing slowly outward -- a steady "listening"
    // texture distinct from the sweep beam below.
    float ringPhase = radius * RING_COUNT - uTime * 0.12;
    float ringDist = abs(fract(ringPhase) - 0.5);
    float ringGlow = 1.0 - smoothstep(0.0, RING_THICKNESS, ringDist);

    // Radial spokes, faded out near the center so they never compete with
    // the source markers (the "markers" group below, rendered as separate
    // meshes).
    float spokeAngle = abs(fract(angle * SPOKE_COUNT / TAU + 0.5) - 0.5) * TAU / SPOKE_COUNT;
    float arcDist = spokeAngle * radius;
    float spokeGlow = (1.0 - smoothstep(0.0, SPOKE_THICKNESS, arcDist)) * smoothstep(0.0, 0.15, radius);

    // Rotating sweep beam -- the primary "actively retrieving" cue,
    // sharper and brighter than the ring/spoke texture underneath it.
    float sweepPhase = uTime * uSweepSpeed;
    float sweepBeam = pow(max(0.5 * sin(angle + sweepPhase) + 0.5, 0.0), SWEEP_WIDTH);

    float edgeFade = smoothstep(1.0, 0.7, radius);
    float intensity = (ringGlow * 0.35 + spokeGlow * 0.3 + sweepBeam * 0.85);
    float alpha = uOpacity * edgeFade * (0.06 + intensity);
    gl_FragColor = vec4(uColor, clamp(alpha, 0.0, 1.0));
  }
`;

/** A radar-style evidence sweep behind the core. */
export function RetrievalScan({ phase, sources }: RetrievalScanProps) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const groupRef = useRef<THREE.Group>(null);
  const currentRef = useRef({ opacity: 0, sweepSpeed: 0 });

  // See `IntelligentParticleField.tsx` for why per-frame writes below go
  // through `materialRef.current.uniforms` rather than this memoized
  // binding directly (the `react-hooks/immutability` lint rule).
  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uSweepSpeed: { value: 0 },
      uOpacity: { value: 0 },
      uColor: { value: new THREE.Color(LIVING_CORE_PHASE_COLOR.idle) },
    }),
    [],
  );
  type ScanUniforms = typeof uniforms;

  const markers = useMemo(
    () =>
      sources.map((source, index) => {
        const angle = getSourceOrbitAngle(index, sources.length);
        return {
          key: source.source_number,
          x: Math.cos(angle) * MARKER_RADIUS,
          y: Math.sin(angle) * MARKER_RADIUS,
        };
      }),
    [sources],
  );

  useFrame(({ clock }, delta) => {
    const material = materialRef.current;
    const group = groupRef.current;
    if (!material || !group) {
      return;
    }

    const materialUniforms = material.uniforms as ScanUniforms;

    const targets = computeScanTargets(phase);
    const dt = Math.min(0.1, Math.max(0, delta));
    const current = currentRef.current;
    current.opacity = damp(current.opacity, targets.opacity, 3.5, dt);
    current.sweepSpeed = damp(current.sweepSpeed, targets.sweepSpeed, 3.5, dt);

    group.visible = phase !== "dormant" && current.opacity > 0.002;
    materialUniforms.uTime.value = clock.getElapsedTime();
    materialUniforms.uSweepSpeed.value = current.sweepSpeed;
    materialUniforms.uOpacity.value = current.opacity;
    materialUniforms.uColor.value.set(LIVING_CORE_PHASE_COLOR[phase]);

    const markerOpacity =
      phase === "converged" ? 0.55 + Math.sin(clock.getElapsedTime() * 1.4) * 0.15 : 0;
    group.children.forEach((child) => {
      if (child instanceof THREE.Mesh && child.userData.isMarker) {
        const mat = child.material as THREE.MeshBasicMaterial;
        mat.opacity = markerOpacity;
      }
    });
  });

  return (
    <group ref={groupRef} position={[0, 0, -0.9]} renderOrder={-1}>
      <mesh>
        <planeGeometry args={[PLANE_RADIUS * 2, PLANE_RADIUS * 2]} />
        <shaderMaterial
          ref={materialRef}
          uniforms={uniforms}
          vertexShader={VERTEX_SHADER}
          fragmentShader={FRAGMENT_SHADER}
          transparent
          depthWrite={false}
          side={THREE.DoubleSide}
        />
      </mesh>
      {markers.map((marker) => (
        <mesh key={marker.key} position={[marker.x, marker.y, 0.01]} userData={{ isMarker: true }}>
          <ringGeometry args={[0.045, 0.06, 24]} />
          <meshBasicMaterial
            color="#7dd3fc"
            transparent
            opacity={0}
            toneMapped={false}
            depthWrite={false}
          />
        </mesh>
      ))}
    </group>
  );
}
