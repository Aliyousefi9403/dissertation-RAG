"use client";

import { Component, useCallback, useEffect, useState, type ReactNode } from "react";
import dynamic from "next/dynamic";
import { useReducedMotion } from "framer-motion";

import type { ChatState } from "@/lib/state/chatMachine";
import type { HealthStatus } from "@/lib/types/health";
import type { SourceItem } from "@/lib/types/chat";
import { getLivingCorePhase, type LivingCorePhase } from "@/lib/living-core/livingCoreState";
import { getLivingCoreStatusText } from "@/lib/living-core/livingCoreCopy";
import { scoreToVisual } from "@/lib/living-core/scoreToVisual";
import { setLivingCoreActivityEnergy } from "@/lib/living-core/livingCoreActivityStore";
import { PARTICLE_COUNT } from "@/lib/living-core/particleBudget";
import { useWebGLSupport } from "@/hooks/useWebGLSupport";
import { useIsNarrowViewport } from "@/hooks/useIsNarrowViewport";
import { useDeviceTier } from "@/hooks/useDeviceTier";
import { LivingCoreStaticFallback } from "@/components/living-core/LivingCoreStaticFallback";
import { AegisMetallicLogo } from "@/components/living-core/AegisMetallicLogo";

interface LivingCoreStageProps {
  chatState: ChatState;
  healthStatus: HealthStatus;
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

// Same phase -> baseline-energy mapping `LivingCoreScene` uses internally,
// duplicated here (cheaply) only to drive the page-root `DotFieldBackdrop`
// reaction via `livingCoreActivityStore` — never re-derived from raw
// `ChatState` a second time, always from the same `phase` this component
// already computed via `getLivingCorePhase`.
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

/**
 * Gates the real living-core 3D scene behind WebGL support and the user's
 * motion preference, wraps it in a runtime error boundary, and always
 * falls back to the pure DOM/CSS `LivingCoreStaticFallback` — critical
 * status information never depends on WebGL succeeding. Same props
 * signature as the retired `shield-core/ShieldCoreStage`, so the
 * page-integration engineer can swap the import in `app/page.tsx` with a
 * single line change.
 *
 * Mobile-viewport decision: narrow viewports still get the real
 * `LivingCoreScene`, just at a lower device-pixel-ratio cap
 * (`useIsNarrowViewport`) and a smaller particle budget
 * (`useDeviceTier`/`particleBudget.ts`), rather than being routed to the
 * static fallback outright.
 */
export function LivingCoreStage({ chatState, healthStatus }: LivingCoreStageProps) {
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

  // Broadcasts the same real-state-derived energy to `DotFieldBackdrop`
  // (mounted separately at the page layout root) regardless of whether the
  // 3D scene itself is rendering — the dot field's "reaction near the
  // core" should stay honest even in reduced-motion/no-WebGL sessions.
  useEffect(() => {
    setLivingCoreActivityEnergy(activityEnergyFor(phase, sources));
  }, [phase, sources]);

  // Conservative gate: `reducedMotion === null` (SSR / not yet measured)
  // and `webglSupport === "checking"` both fall through to the static
  // fallback — the safe default is always the DOM/CSS version, never the
  // 3D scene.
  const canRender3D =
    webglSupport === "supported" && reducedMotion === false && !runtimeFailure;

  if (!canRender3D) {
    return <LivingCoreStaticFallback phase={phase} sources={sources} detail={detail} />;
  }

  // The caption is a flow sibling of the canvas wrapper, not an overlay
  // absolutely positioned inside it — see the long comment on
  // `.living-core-status-caption` in globals.css for why: an overlay
  // pinned to the bottom of the wrapper collides with the shield's lower
  // point once the wrapper is short (compact/mobile), since the shield's
  // on-screen size is driven by a fixed camera FOV, not the wrapper's
  // pixel height.
  return (
    <>
      {/* `.living-core-canvas-frame` is a plain unstyled-size positioning
          shell around `.living-core-canvas-wrap` (which keeps 100% of its
          existing sizing/border/background rules unchanged) so the
          metallic emblem badge below can sit as a DOM SIBLING of the r3f
          canvas rather than a child inside `.living-core-canvas-wrap` --
          keeps "exactly one canvas inside `.living-core-canvas-wrap`" true
          for `e2e/desktop.spec.ts`'s existing locator, and keeps the r3f
          `<Canvas>`/`DotFieldBackdrop` pair the only two canvases anyone
          needs to reason about as "the app's WebGL surfaces". */}
      <div className="living-core-canvas-frame">
        <div className="living-core-canvas-wrap">
          <LivingCoreErrorBoundary onError={handleRuntimeFailure}>
            <DynamicLivingCoreScene
              phase={phase}
              sources={sources}
              maxDpr={isNarrowViewport ? 1 : 1.5}
              particleCount={PARTICLE_COUNT[deviceTier]}
              onRuntimeFailure={handleRuntimeFailure}
            />
          </LivingCoreErrorBoundary>
        </div>
        {/* A thin metallic emblem "shell" -- a secondary framing element
            echoing the sidebar's static AegisRAG mark, never the primary
            object (the GPU particle field above remains dominant). See
            `AegisMetallicLogo.tsx`'s header comment. */}
        <AegisMetallicLogo size={40} className="living-core-metallic-shell" />
      </div>
      <p
        className="living-core-status-caption"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {getLivingCoreStatusText(phase, sources.length, detail)}
      </p>
    </>
  );
}
