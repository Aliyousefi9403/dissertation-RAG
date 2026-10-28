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
 * Keeps the demand-mode render loop alive only while (a) the tab is visible
 * and (b) the current phase/choreography beat is meant to animate
 * continuously. "dormant" and a settled "converged" render one static frame
 * per prop change and then sit still until something actually changes —
 * that stillness is itself the visual cue that nothing further is
 * happening. The `visibilitychange` check is new versus the retired
 * `shield-core/ShieldCoreScene.tsx`, which had no hidden-tab pause at all:
 * a backgrounded tab now stops invalidating frames entirely, regardless of
 * `active`.
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

// Zoomed in from the previous z=5.4 (fov unchanged at 40) so the rendered
// particle-field silhouette fills roughly the product brief's 35-50% target
// share of the `.living-core-canvas-wrap` frame — a pure camera-distance
// change, so it scales the whole scene uniformly and never desyncs
// `particleBudget.ts`'s `LAYER_RADII` from `sourceLayout.ts`'s orbit radii
// the way an isolated geometry-scale bump could.
//
// The small negative y here shifts the whole field up within the frame:
// r3f's default camera calls `camera.lookAt(0, 0, 0)` exactly ONCE, at
// creation, computed from the Canvas `camera` prop's initial position below
// (which is deliberately left at the untilted [0, 0, 4.8], not this offset
// -- see that prop's comment) -- so rotation is fixed "straight down -Z"
// from that point on, and every later `camera.position.set(...)` below
// (IdleCameraDrift) is a genuine parallax translate, not re-centered by a
// fresh lookAt. (Verified empirically: setting the initial Canvas position
// to this same offset made r3f's one-time lookAt tilt to compensate,
// silently cancelling the shift entirely.)
const CAMERA_BASE_POSITION = new THREE.Vector3(0, -0.14, 4.8);

// Phase-driven bloom targets -- `BloomComposer` damps toward whichever of
// these is passed each frame, so switching phases here reads as a smooth
// cinematic ramp rather than a pop. Base idle/dormant/unresolved/fault
// values match `BloomComposer`'s own defaults.
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

/**
 * The only camera motion anywhere in the scene: a very slow, subtle
 * position drift, active only while "idle" — never a rotation, never
 * looped fast enough to read as spinning, and never tied to page scroll.
 * Because the camera is otherwise on-axis and pointed at the origin with
 * no explicit look-at target, a small position offset alone produces a
 * gentle parallax cue without any rotation math.
 */
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

/**
 * r3f root for the living-core hero visualization. This is a fixed hero
 * object, not an interactive toy: no `OrbitControls`, no click/hover
 * handlers, fixed camera. Combined with `aria-hidden="true"` on the
 * canvas, the 3D subtree is fully removed from the accessibility tree and
 * cannot trap keyboard focus — the real status text lives in
 * `LivingCoreStage`'s DOM caption, never inside the canvas.
 *
 * The centerpiece is `IntelligentParticleField`, a real GPU particle
 * simulation replacing both the retired static `ShieldOutline` mesh and the
 * retired FBO-ping-pong `NeuralPointCloud` — no shield-forming behavior
 * yet (deliberately future work), just the "waiting for input" intelligent
 * cloud. `BloomComposer` renders the whole scene through a manual
 * `EffectComposer` (three's own bundled postprocessing passes, no new
 * dependency) instead of the default r3f render, and `RetrievalScan` shares
 * this same camera/depth space (never a second canvas — that's
 * `DotFieldBackdrop`'s bounded exception, mounted separately at the page
 * layout root).
 */
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

  // Presentation-only sequencing for the entire "submitting" duration and
  // for the moment a request resolves (see `useLivingCoreChoreography`) —
  // never gates the real answer/status text, which live entirely outside
  // this canvas in `LivingCoreStage`.
  const { beat, beatStartedAt } = useLivingCoreChoreography({ phase });
  const isChoreographyPlaying =
    beat === "retrieving" || beat === "generating" || beat === "arriving" || beat === "linking";

  return (
    <Canvas
      aria-hidden="true"
      // r3f's <Canvas> defaults its wrapper div to inline `pointer-events:
      // auto` (see CanvasImpl in @react-three/fiber) whenever no
      // `eventSource` is supplied, specifically so raycasting/pointer
      // events reach the 3D scene. That inline style wins over any CSS
      // class rule (including `.living-core-canvas-frame`'s `pointer-
      // events: none`), which was silently capturing clicks meant for the
      // topbar/experiment-mode selector above this fullscreen ambient
      // backdrop. This scene has no interactive 3D pointer handling, so
      // it's overridden back to `none` here (r3f spreads a `style` prop
      // after its own defaults, so this wins cleanly, no `!important`
      // needed) — purely non-visual, no effect on the rendered scene.
      style={{ pointerEvents: "none" }}
      dpr={[1, maxDpr]}
      frameloop="demand"
      gl={{ antialias: false, powerPreference: "high-performance" }}
      // Deliberately NOT CAMERA_BASE_POSITION -- this initial position is
      // what r3f's default camera uses for its one-time `lookAt(0, 0, 0)`
      // at creation (see CAMERA_BASE_POSITION's comment above); staying at
      // the untilted origin position here keeps that computed rotation
      // "straight down -Z", which IdleCameraDrift's later position updates
      // then rely on to actually shift the frame rather than re-center it.
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
