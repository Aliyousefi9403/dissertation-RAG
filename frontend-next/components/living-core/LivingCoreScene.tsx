"use client";

import { useEffect, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

import { isAnimatedPhase, type LivingCorePhase } from "@/lib/living-core/livingCoreState";
import { useLivingCoreChoreography } from "@/lib/living-core/useLivingCoreChoreography";
import type { SourceItem } from "@/lib/types/chat";
import { IntelligentParticleField } from "@/components/living-core/IntelligentParticleField";
import { BloomComposer } from "@/components/living-core/BloomComposer";
import { NeuralConnections } from "@/components/living-core/NeuralConnections";
import { RetrievalScan } from "@/components/living-core/RetrievalScan";
import { SourceNodes } from "@/components/living-core/SourceNodes";
import { SourceLinkPaths } from "@/components/living-core/SourceLinkPaths";

interface LivingCoreSceneProps {
  phase: LivingCorePhase;
  sources: SourceItem[];
  /** Upper device-pixel-ratio bound; the caller lowers this on narrow
   * viewports to keep fill-rate cost down (see `LivingCoreStage`). */
  maxDpr: number;
  /** Particle count for `IntelligentParticleField`'s GPU field, chosen by
   * `LivingCoreStage` from `particleBudget.ts` via `useDeviceTier` — always
   * within the 15,000-30,000 range. */
  particleCount: number;
  onRuntimeFailure: () => void;
  /** Forwarded to `IntelligentParticleField` — see its own doc comment. */
  attackDetected?: boolean;
  /** Forwarded to `IntelligentParticleField` — see its own doc comment. */
  compareMode?: boolean;
  /** Defence-mode edge colour, forwarded to `IntelligentParticleField`. */
  tint?: string | null;
}

/**
 * Keeps the demand-mode render loop alive only while the tab is visible and the current
 * phase/choreography beat is meant to animate continuously.
 */
function FrameLoopDriver({ active }: { active: boolean }) {
  const isVisibleRef = useRef(true);

  useEffect(() => {
    function handleVisibilityChange() {
      isVisibleRef.current = document.visibilityState === "visible";
    }
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, []);

  useFrame(({ invalidate }) => {
    if (active && isVisibleRef.current) {
      invalidate();
    }
  });
  return null;
}

// Zoomed in from the previous z=5.4 so the rendered particle-field silhouette fills roughly the
// product brief's 35-50% target share of the `.living-core-canvas-wrap` frame.
const CAMERA_BASE_POSITION = new THREE.Vector3(0, -0.14, 4.8);

// Phase-driven bloom targets.
const BLOOM_BY_PHASE: Record<
  LivingCorePhase,
  { strength: number; radius: number; threshold: number }
> = {
  dormant: { strength: 1.2, radius: 0.8, threshold: 0.2 },
  idle: { strength: 1.2, radius: 0.8, threshold: 0.2 },
  submitting: { strength: 1.6, radius: 0.85, threshold: 0.16 },
  converged: { strength: 1.5, radius: 0.82, threshold: 0.18 },
  unresolved: { strength: 1.2, radius: 0.8, threshold: 0.2 },
  fault: { strength: 1.2, radius: 0.8, threshold: 0.2 },
};

/** The only camera motion anywhere in the scene: a very slow, subtle position drift. */
function IdleCameraDrift({ active }: { active: boolean }) {
  const { camera } = useThree();

  useFrame(({ clock }) => {
    if (!active) {
      camera.position.copy(CAMERA_BASE_POSITION);
      return;
    }
    const elapsed = clock.getElapsedTime();
    camera.position.set(
      CAMERA_BASE_POSITION.x + Math.sin(elapsed * 0.15) * 0.05,
      CAMERA_BASE_POSITION.y + Math.cos(elapsed * 0.11) * 0.03,
      CAMERA_BASE_POSITION.z,
    );
  });

  return null;
}

/** R3f root for the living-core hero visualization. */
export function LivingCoreScene({
  phase,
  sources,
  maxDpr,
  particleCount,
  onRuntimeFailure,
  attackDetected = false,
  compareMode = false,
  tint = null,
}: LivingCoreSceneProps) {
  const visibleSources = phase === "converged" ? sources : [];

  // Presentation-only sequencing for the entire "submitting" duration and for the moment a
  // request resolves.
  const { beat, beatStartedAt } = useLivingCoreChoreography({ phase });
  const isChoreographyPlaying =
    beat === "retrieving" || beat === "generating" || beat === "arriving" || beat === "linking";

  return (
    <Canvas
      aria-hidden="true"
      // R3f's <Canvas> defaults its wrapper div to inline `pointer-events: auto` whenever no
      // `eventSource` is supplied, specifically so raycasting/pointer events reach the 3D
      // scene.
      style={{ pointerEvents: "none" }}
      dpr={[1, maxDpr]}
      frameloop="demand"
      gl={{ antialias: false, powerPreference: "high-performance" }}
      // Deliberately NOT CAMERA_BASE_POSITION.
      camera={{ position: [0, 0, 4.8], fov: 40, near: 0.1, far: 20 }}
      onCreated={({ gl }) => {
        gl.domElement.addEventListener(
          "webglcontextlost",
          (event) => {
            event.preventDefault();
            onRuntimeFailure();
          },
          { passive: false },
        );
      }}
    >
      {/* Very dark, fully opaque scene background — set explicitly on the
          scene (rather than left transparent over the CSS wrap background)
          so it's guaranteed regardless of DOM layering, and so the bloom
          pass composites against genuine near-black rather than whatever
          happens to sit behind the canvas. */}
      <color attach="background" args={["#05070d"]} />
      {/* Ambient + a soft, low-intensity directional fill (not a single
          hard key light) for any lit materials elsewhere in this scene —
          `IntelligentParticleField`'s own shader is unlit. */}
      <ambientLight intensity={0.65} />
      <directionalLight position={[2.5, 3, 4]} intensity={0.4} />
      <directionalLight position={[-2.5, -1.5, 3]} intensity={0.22} />
      <FrameLoopDriver active={isAnimatedPhase(phase) || isChoreographyPlaying} />
      <IdleCameraDrift active={phase === "idle"} />
      <RetrievalScan phase={phase} sources={visibleSources} />
      <NeuralConnections phase={phase} />
      <IntelligentParticleField
        phase={phase}
        particleCount={particleCount}
        attackDetected={attackDetected}
        compareMode={compareMode}
        tint={tint}
      />
      <SourceNodes sources={visibleSources} beat={beat} beatStartedAt={beatStartedAt} />
      <SourceLinkPaths sources={visibleSources} beat={beat} beatStartedAt={beatStartedAt} />
      <BloomComposer {...BLOOM_BY_PHASE[phase]} />
    </Canvas>
  );
}
