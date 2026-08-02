# Living core states

The living-core visualization (`components/living-core/LivingCoreStage.tsx`
and its 3D implementation, `components/living-core/LivingCoreScene.tsx`) is
driven entirely by two pieces of real, observable state: `ChatState` (from
`lib/state/chatMachine.ts`) and `HealthStatus` (from
`lib/types/health.ts`). It must never display anything that isn't derived
from those two sources — no fabricated trust, confidence, poisoning, or
defence metrics.

This document supersedes the retired `docs/frontend/shield-core-states.md`.
Every hard rule below is unchanged from that document; only component/file
names have been updated, and two new presentation-only choreography
sub-beats have been documented (see "Choreography beats" below).

| State | Trigger | What is shown | What must never be shown |
| --- | --- | --- | --- |
| `idle` | Initial load, or after a `RESET` event. No question submitted yet. | A calm, resting visual. May reflect `healthStatus` (e.g. dimmed/inactive look while `offline` or `checking`). | Any activity, retrieval, or "processing" motion. No numeric scores. |
| `submitting` | User submitted a question; awaiting `/chat` response. | An active/"thinking" animation communicating that retrieval and generation are in progress. Should be tied to `aria-live="polite"` text already present in `AnswerPanel`, not duplicate a competing announcement. | Any source count, similarity score, or answer content — none exist yet. No claim of "verifying" or "checking integrity" that isn't literally happening. No numbered source badges — real source numbers do not exist until the response arrives (see "Choreography beats"). |
| `success` | `/chat` returned `sources.length > 0`. | A visual response to the real `sources` array — e.g. node/path count and `RetrievalScan` marker count proportional to `sources.length`, and any per-source visual weighting must be derived only from the real `score` field (labelled internally as "similarity score", never "confidence" or "trust"). | Any bar, gauge, or color scale that implies calibrated confidence. No invented categories (e.g. "high/medium/low trust"). |
| `noSources` | `/chat` returned `sources.length === 0` with a real `answer`. This is a valid, successful outcome — not an error. | A visual state clearly distinct from both `success` and `error` — an empty/hollow, diffuse point-cloud read (see `NeuralPointCloud`'s "unresolved" targets) and no `RetrievalScan` markers — honestly reflecting that no grounding evidence was retrieved. | Do not reuse the `success` visual (would misrepresent evidence that doesn't exist). Do not reuse the `error` visual (this is not a failure). No fabricated placeholder sources. |
| `error` | The request failed (`REQUEST_FAILED`): validation error, server error, network error, or timeout. | A visual state clearly communicating failure, paired with the real `message` text already rendered by `AnswerPanel` — a brief loss of coherence (see `NeuralPointCloud`'s fault flicker window) settling into a static, muted-red "controlled fault" state. | No specific backend internals beyond the real error message. No retry countdown or diagnostic detail that wasn't returned by the API. No explosion/alarm-style motion. |

## Phase vocabulary

`lib/living-core/livingCoreState.ts`'s `getLivingCorePhase` is the ONLY
function allowed to read raw `ChatState`/`HealthStatus` fields for
living-core visual purposes, and derives one of six `LivingCorePhase`
values: `dormant` (backend offline — always wins over any other state),
`idle`, `submitting`, `converged` (= `success`), `unresolved` (=
`noSources`), `fault` (= `error`). This derivation is unchanged from the
retired `shieldCoreState.ts`'s `getShieldCorePhase`/`ShieldCorePhase` — only
the names moved.

## Choreography beats (presentation-only, non-gating)

`lib/living-core/useLivingCoreChoreography.ts` sequences short rendering
beats on top of `LivingCorePhase`. None of these are new `ChatState`/phase
values, and none of them gate the real answer/status text — that text
(`LivingCoreStage`'s `aria-live` caption, and `AnswerPanel`) reads `phase`
directly and updates the instant the real state changes, never waiting on
any beat below.

- **`idle`** — resting beat for `dormant`/`idle`/`unresolved`/`fault`. No
  sequencing; each phase's own ambient motion (breathing, drift, fault
  flicker) plays from its own timers.
- **`retrieving` / `generating`** — a looping two-stage sub-sequence that
  only plays while `phase === "submitting"`. There is no backend-level
  distinction between "retrieving" and "generating" — `POST /chat` is one
  non-streaming call — so this is purely an ambient rendering cadence
  (anonymous energy pulsing inward toward the core during "retrieving",
  then the core visibly compressing/brightening at its center during
  "generating"), not a claim about literal backend stages. It loops for as
  long as "submitting" actually lasts, however long the real request
  takes. **Hard rule: during both sub-beats, every living-core component
  renders only anonymous energy/pulses — never a numbered source badge or
  `RetrievalScan` marker**, since real source numbers do not exist until
  the response arrives.
- **`arriving` / `linking` / `resolved`** — the pre-existing
  converged-phase sequence (source nodes easing inward from a wider radius
  into their resting formation, then evidence energy visibly flowing from
  each node into the core, then settling into a steady state), unchanged
  in behavior and duration from the retired `useShieldChoreography.ts`'s
  identical beats.

## Cross-cutting rules

- The living core must react only to `chatState.status` and `healthStatus`;
  it must not maintain its own hidden interpretation of "security posture."
- Any numeric value visualized (e.g. point-cloud energy, node count, path
  density, `RetrievalScan` marker count) must trace back to a real field on
  `ChatResponse` (`sources.length`, `sources[].score`) or to the derived
  `LivingCorePhase` itself. Never invent a metric that isn't in the backend
  contract.
- `hooks/useDeviceTier.ts`'s device-tier estimate (`desktop` / `mobile` /
  `low-power`) is a **rendering-cost heuristic only** — it exists purely to
  pick a particle-count budget (`lib/living-core/particleBudget.ts`) and
  must never be read, displayed, or treated as a security, trust, or
  defence signal anywhere in the app.
- `RetrievalScan` is explicitly named "Retrieval Scan" (or "Evidence Scan")
  in any UI copy — never "Attack Detection" or any other threat-scanning
  framing. Its sweep is decorative and reflects retrieval activity only.
- All animation must respect `prefers-reduced-motion` and avoid
  scroll-hijacking. `LivingCoreStage` and `DotFieldBackdrop` both fall back
  to a static, non-animated presentation when
  `prefers-reduced-motion: reduce` is set (or, for `LivingCoreStage`, when
  WebGL is unsupported or the 3D scene throws at runtime) rather than
  playing a "reduced" version of the same animation.
- Both the living-core canvas (`LivingCoreScene`) and the page-root
  `DotFieldBackdrop` canvas stop doing per-frame work while the tab is
  hidden (`document.visibilitychange`) — see `FrameLoopDriver` in
  `LivingCoreScene.tsx` and the `visibilitychange` handling in
  `DotFieldBackdrop.tsx`.
- Text equivalents of state must always exist in the DOM (via `StatusBar`
  and `AnswerPanel`, plus `LivingCoreStage`'s own `aria-live` caption) — the
  3D visualization (and the dot-field backdrop) are supplementary,
  non-exclusive channels, never the only source of truth for a state.
- `DotFieldBackdrop`'s subtle "reaction near the core" reads a broadcast
  energy value (`lib/living-core/livingCoreActivityStore.ts`) that mirrors
  the same phase-derived energy `LivingCoreStage` already computes — it is
  a presentation-only pub/sub, not a second, independent interpretation of
  chat state, and it never renders any text/number.
