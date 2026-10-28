"use client";

import { Component, useCallback, useEffect, useState, type ReactNode } from "react";
import dynamic from "next/dynamic";
import { useReducedMotion } from "framer-motion";

import type { ChatState } from "@/lib/state/chatMachine";
import type { HealthStatus } from "@/lib/types/health";
import type { SourceItem } from "@/lib/types/chat";
import { getLivingCorePhase, type LivingCorePhase } from "@/lib/living-core/livingCoreState";
import { scoreToVisual } from "@/lib/living-core/scoreToVisual";
import { setLivingCoreActivityEnergy } from "@/lib/living-core/livingCoreActivityStore";
import { PARTICLE_COUNT } from "@/lib/living-core/particleBudget";
import { useWebGLSupport } from "@/hooks/useWebGLSupport";
import { useIsNarrowViewport } from "@/hooks/useIsNarrowViewport";
import { useDeviceTier } from "@/hooks/useDeviceTier";
import { LivingCoreStaticFallback } from "@/components/living-core/LivingCoreStaticFallback";
import { EnergyBeams } from "@/components/living-core/EnergyBeams";
import { SourcePins } from "@/components/living-core/SourcePins";
import { DefenceShield } from "@/components/living-core/DefenceShield";
import {
  ContextLensEmblem,
  MonitorGate,
  RepairLoom,
} from "@/components/living-core/DefenceEmblems";
import type { MonitorTrace } from "@/lib/types/monitor";

export type DefenceMode = "defended" | "repaired" | "contextual" | "verified";

/** Particle edge colour per defence mode. */
const DEFENCE_TINT: Record<DefenceMode, string> = {
  defended: "#4fd18b",
  repaired: "#f2b54a",
  contextual: "#a98bff",
  verified: "#2fe0c0",
};
import {
  repairedWordCount,
  skippedPassageCount,
  type ShieldState,
} from "@/lib/living-core/defenceShield";

interface LivingCoreStageProps {
  chatState: ChatState;
  healthStatus: HealthStatus;
  /** True while PWWS Poisoned mode is selected in `app/page.tsx`'s experiment-mode selector. */
  attackDetected?: boolean;
  /** Forwarded to `LivingCoreScene` — see its own doc comment. */
  compareMode?: boolean;
  /** The selected defence mode, if any: each has its own centrepiece and particle colour. */
  defence?: DefenceMode | null;
  /** Verified mode: the runtime monitor's trace for the last answer. */
  monitor?: MonitorTrace | null;
}

function shieldStateFor(phase: LivingCorePhase): ShieldState {
  if (phase === "submitting") {
    return "scanning";
  }
  if (phase === "fault") {
    return "fault";
  }
  if (phase === "converged" || phase === "unresolved") {
    return "resolved";
  }
  return "armed";
}

// Loaded only once WebGL support + motion checks pass, so the three.js /
// @react-three/* module graph never enters the bundle-eval path for
// reduced-motion or unsupported-WebGL sessions.
const DynamicLivingCoreScene = dynamic(
  () => import("@/components/living-core/LivingCoreScene").then((module) => module.LivingCoreScene),
  {
    ssr: false,
    loading: () => <div className="living-core-canvas-loading" aria-hidden="true" />,
  },
);

class LivingCoreErrorBoundary extends Component<
  { onError: () => void; children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch() {
    this.props.onError();
  }

  render() {
    if (this.state.hasError) {
      // The parent flips `runtimeFailure` (via `onError`) and swaps to
      // `LivingCoreStaticFallback` on its next render; render nothing for
      // the one frame in between rather than a half-broken canvas.
      return null;
    }
    return this.props.children;
  }
}

function extractSources(chatState: ChatState): SourceItem[] {
  return chatState.status === "success" ? chatState.sources : [];
}

// Same phase -> baseline-energy mapping `LivingCoreScene` uses internally.
function activityEnergyFor(phase: LivingCorePhase, sources: SourceItem[]): number {
  if (phase === "dormant") {
    return 0;
  }
  if (phase === "converged") {
    if (sources.length === 0) {
      return 0.4;
    }
    const total = sources.reduce((sum, source) => sum + scoreToVisual(source.score), 0);
    return Math.max(0.35, total / sources.length);
  }
  if (phase === "submitting") {
    return 0.55;
  }
  if (phase === "fault") {
    return 0.3;
  }
  if (phase === "unresolved") {
    return 0.2;
  }
  return 0.3; // idle
}

/** Gates the real living-core 3D scene behind WebGL support and the user's motion preference. */
export function LivingCoreStage({
  chatState,
  healthStatus,
  attackDetected = false,
  compareMode = false,
  defence = null,
  monitor = null,
}: LivingCoreStageProps) {
  const phase = getLivingCorePhase(chatState, healthStatus);
  const sources = extractSources(chatState);
  const detail = chatState.status === "error" ? chatState.message : undefined;

  const webglSupport = useWebGLSupport();
  const reducedMotion = useReducedMotion();
  const isNarrowViewport = useIsNarrowViewport();
  const deviceTier = useDeviceTier();
  const [runtimeFailure, setRuntimeFailure] = useState(false);

  const handleRuntimeFailure = useCallback(() => {
    setRuntimeFailure(true);
  }, []);

  // Broadcasts the same real-state-derived energy to `DotFieldBackdrop` regardless of whether
  // the 3D scene itself is rendering.
  useEffect(() => {
    setLivingCoreActivityEnergy(activityEnergyFor(phase, sources));
  }, [phase, sources]);

  // Conservative gate: `reducedMotion === null` and `webglSupport === "checking"` both fall
  // through to the static fallback.
  const canRender3D = webglSupport === "supported" && reducedMotion === false && !runtimeFailure;

  const emblemState = shieldStateFor(phase);
  const variant = canRender3D ? "stage" : "inline";
  const shield =
    defence === "defended" ? (
      <DefenceShield state={emblemState} skipped={skippedPassageCount(sources)} variant={variant} />
    ) : defence === "repaired" ? (
      <RepairLoom state={emblemState} variant={variant} repaired={repairedWordCount(sources)} />
    ) : defence === "contextual" ? (
      <ContextLensEmblem
        state={emblemState}
        variant={variant}
        skipped={skippedPassageCount(sources)}
      />
    ) : defence === "verified" ? (
      <MonitorGate state={emblemState} variant={variant} trace={monitor} />
    ) : null;

  if (!canRender3D) {
    return (
      <>
        {shield}
        <LivingCoreStaticFallback phase={phase} sources={sources} detail={detail} />
      </>
    );
  }

  return (
    <div className="living-core-canvas-frame" data-defended={defence !== null}>
      <div className="living-core-canvas-wrap">
        <LivingCoreErrorBoundary onError={handleRuntimeFailure}>
          <DynamicLivingCoreScene
            phase={phase}
            sources={sources}
            maxDpr={isNarrowViewport ? 1 : 1.5}
            particleCount={PARTICLE_COUNT[deviceTier]}
            onRuntimeFailure={handleRuntimeFailure}
            attackDetected={attackDetected}
            compareMode={compareMode}
            tint={defence ? DEFENCE_TINT[defence] : null}
          />
        </LivingCoreErrorBoundary>
      </div>
      <EnergyBeams />
      <SourcePins sources={sources} />
      {shield}
    </div>
  );
}
