"use client";

import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

import type { SourceItem } from "@/lib/types/chat";
import { LIVING_CORE_PHASE_COLOR } from "@/lib/living-core/livingCorePalette";
import { CORE_ANCHOR_RADIUS, getSourceFormationPosition } from "@/lib/living-core/sourceLayout";
import type { LivingCoreChoreographyBeat } from "@/lib/living-core/useLivingCoreChoreography";

interface SourceLinkPathsProps {
  sources: SourceItem[];
  beat: LivingCoreChoreographyBeat;
  beatStartedAt: number;
}

/**
 * One evidence path per real retrieved source (count is always exactly
 * `sources.length` — this component never invents a node or a path). Each
 * path connects that source's settled formation position (the same
 * `getSourceFormationPosition` helper `SourceNodes` uses, so the two
 * always agree on where a node sits) to the core.
 *
 * Energy only visibly travels inward along a path during the "linking"
 * choreography beat (see `useLivingCoreChoreography`); every other beat
 * renders the same static lines at a settled opacity. This is a rendering
 * sequence only — it never gates when the real answer/sources become
 * available. Renamed 1:1 from the retired `shield-core/SourceLinkPaths.tsx`.
 */
export function SourceLinkPaths({ sources, beat, beatStartedAt }: SourceLinkPathsProps) {
  const lineRef = useRef<THREE.LineSegments>(null);
  const materialRef = useRef<THREE.LineDashedMaterial>(null);
  const baseDistancesRef = useRef<Float32Array | null>(null);

  const geometry = useMemo(() => {
    const positions: number[] = [];
    sources.forEach((_source, index) => {
      const target = getSourceFormationPosition(index, sources.length);
      const inward = target.clone().normalize().multiplyScalar(CORE_ANCHOR_RADIUS);
      positions.push(inward.x, inward.y, inward.z, target.x, target.y, target.z);
    });
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    return geom;
  }, [sources]);

  useEffect(() => {
    const line = lineRef.current;
    if (!line) {
      return;
    }
    line.computeLineDistances();
    const lineDistance = line.geometry.getAttribute("lineDistance") as
      | THREE.BufferAttribute
      | undefined;
    baseDistancesRef.current = lineDistance
      ? Float32Array.from(lineDistance.array as Float32Array)
      : null;
  }, [geometry]);

  useFrame(() => {
    const line = lineRef.current;
    const material = materialRef.current;
    const baseDistances = baseDistancesRef.current;
    if (!line || !material || sources.length === 0) {
      return;
    }

    material.color.set(LIVING_CORE_PHASE_COLOR.converged);

    const lineDistance = line.geometry.getAttribute("lineDistance") as
      | THREE.BufferAttribute
      | undefined;

    // Negative (decreasing) offset shifts the dash pattern from the outer
    // endpoint toward the core — i.e. inward — the mirror of
    // `NeuralConnections`' outward flow during "submitting".
    const flowOffset = beat === "linking" ? -((performance.now() - beatStartedAt) / 1000) * 2.6 : 0;

    if (lineDistance && baseDistances) {
      const array = lineDistance.array as Float32Array;
      let changed = false;
      for (let i = 0; i < array.length; i += 1) {
        const next = baseDistances[i] + flowOffset;
        if (array[i] !== next) {
          array[i] = next;
          changed = true;
        }
      }
      if (changed) {
        lineDistance.needsUpdate = true;
      }
    }

    if (beat === "arriving") {
      material.opacity = 0.06;
    } else if (beat === "linking") {
      material.opacity = 0.75;
    } else {
      // "resolved": paths stay visible/legible at rest, just without the
      // travelling pulse — the relationship persists, not just the
      // transient animation.
      material.opacity = 0.4;
    }
  });

  if (sources.length === 0) {
    return null;
  }

  return (
    <lineSegments ref={lineRef} geometry={geometry} frustumCulled={false} renderOrder={3}>
      <lineDashedMaterial
        ref={materialRef}
        transparent
        depthWrite={false}
        dashSize={0.1}
        gapSize={0.08}
        opacity={0.06}
        toneMapped={false}
      />
    </lineSegments>
  );
}
