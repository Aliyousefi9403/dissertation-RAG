"use client";

import { useMemo, useRef, type CSSProperties } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";

import type { SourceItem } from "@/lib/types/chat";
import { scoreToVisual } from "@/lib/living-core/scoreToVisual";
import {
  getSourceArrivalStartPosition,
  getSourceFormationPosition,
} from "@/lib/living-core/sourceLayout";
import { DEFAULT_ARRIVING_MS } from "@/lib/living-core/useLivingCoreChoreography";
import type { LivingCoreChoreographyBeat } from "@/lib/living-core/useLivingCoreChoreography";

interface SourceNodesProps {
  sources: SourceItem[];
  beat: LivingCoreChoreographyBeat;
  beatStartedAt: number;
}

const NODE_COLOR = "#7dd3fc";
const NODE_RADIUS = 0.1;
const MIN_SCALE = 0.55;
const MAX_SCALE = 1.25;

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

const LABEL_STYLE: CSSProperties = {
  width: 18,
  height: 18,
  borderRadius: "50%",
  background: "rgba(8, 15, 26, 0.72)",
  border: "1px solid rgba(125, 211, 252, 0.65)",
  color: "#e6f6ff",
  fontSize: 10,
  fontWeight: 600,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontFamily: "inherit",
  userSelect: "none",
  opacity: 0,
  transition: "opacity 160ms linear",
};

/**
 * One small instanced node per real retrieved `SourceItem`, keyed by
 * `source_number` — the caller (`LivingCoreScene`) only ever passes a
 * non-empty `sources` array during "converged"; every other phase
 * (including the pre-response "retrieving"/"generating" sub-beats of
 * "submitting") passes `[]`, and this component never renders a
 * placeholder: zero sources means zero nodes, always. Node
 * scale/color-mix is driven only by the real `score` field via
 * `scoreToVisual` — a rendering intensity, never a "confidence" figure.
 *
 * During the "arriving" choreography beat, nodes ease inward from a wider
 * starting radius into their resting formation
 * (`getSourceFormationPosition`) — the same position `SourceLinkPaths`
 * anchors its lines to, and `RetrievalScan` derives its marker angle from
 * (via `getSourceOrbitAngle`), so all three always agree. Each node also
 * gets a small numeral badge (via drei's `Html`) matching its real
 * `source_number`, so every node is traceable back to a specific source —
 * marked `aria-hidden` since it is a decorative restatement of information
 * the DOM fallback and answer panel already expose as real accessible
 * text. Renamed 1:1 from the retired `shield-core/SourceNodes.tsx`.
 */
export function SourceNodes({ sources, beat, beatStartedAt }: SourceNodesProps) {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const labelRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const geometry = useMemo(() => new THREE.IcosahedronGeometry(NODE_RADIUS, 1), []);

  const nodeData = useMemo(
    () =>
      sources.map((source, index) => ({
        source,
        intensity: scoreToVisual(source.score),
        start: getSourceArrivalStartPosition(index, sources.length),
        end: getSourceFormationPosition(index, sources.length),
      })),
    [sources],
  );

  useFrame(() => {
    const mesh = meshRef.current;
    if (!mesh || nodeData.length === 0) {
      return;
    }

    const progress =
      beat === "arriving" ? Math.min(1, (performance.now() - beatStartedAt) / DEFAULT_ARRIVING_MS) : 1;
    const eased = easeOutCubic(progress);
    const labelOpacity = Math.max(0, (eased - 0.35) / 0.65);

    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    const scaleVector = new THREE.Vector3();
    const baseColor = new THREE.Color(NODE_COLOR);
    const white = new THREE.Color("#ffffff");

    nodeData.forEach(({ intensity, start, end }, index) => {
      position.lerpVectors(start, end, eased);
      const targetScale = MIN_SCALE + intensity * (MAX_SCALE - MIN_SCALE);
      scaleVector.setScalar(targetScale * (0.5 + eased * 0.5));
      matrix.compose(position, quaternion, scaleVector);
      mesh.setMatrixAt(index, matrix);

      const color = baseColor.clone().lerp(white, intensity * 0.55);
      mesh.setColorAt(index, color);

      const label = labelRefs.current[index];
      if (label) {
        label.style.opacity = String(labelOpacity);
      }
    });

    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) {
      mesh.instanceColor.needsUpdate = true;
    }
  });

  if (sources.length === 0) {
    return null;
  }

  return (
    <group>
      <instancedMesh
        ref={meshRef}
        args={[geometry, undefined, sources.length]}
        frustumCulled={false}
        renderOrder={4}
      >
        <meshStandardMaterial
          color={NODE_COLOR}
          roughness={0.3}
          metalness={0.05}
          toneMapped={false}
        />
      </instancedMesh>
      {nodeData.map(({ source, end }, index) => (
        <Html
          key={source.source_number}
          position={[end.x, end.y, end.z]}
          center
          sprite
          distanceFactor={6}
          pointerEvents="none"
          aria-hidden="true"
        >
          <span
            ref={(el) => {
              labelRefs.current[index] = el;
            }}
            style={LABEL_STYLE}
          >
            {source.source_number}
          </span>
        </Html>
      ))}
    </group>
  );
}
