"use client";

import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

import type { LivingCorePhase } from "@/lib/living-core/livingCoreState";
import { LIVING_CORE_PHASE_COLOR } from "@/lib/living-core/livingCorePalette";

interface NeuralConnectionsProps {
  phase: LivingCorePhase;
}

const PATH_COUNT = 3;
const CORE_ANCHOR_RADIUS = 0.5;
const OUTER_ANCHOR_RADIUS = 1.4;

/**
 * Evenly spreads `count` unit directions using a golden-angle spiral —
 * cheap, deterministic, and avoids the pole-clustering a naive
 * latitude/longitude grid would produce for such a small count.
 *
 * Unlike the retired `NeuralPaths.tsx` (whose anchors had to stay within a
 * solid extruded shield's thin z-depth), `ShieldOutline` is now a flat
 * silhouette with nothing to poke through, so these anchors are free to use
 * real 3D spread — contributing to the point cloud's volumetric read
 * instead of being pinned near a single plane.
 */
function evenlySpreadDirections(count: number): THREE.Vector3[] {
  const directions: THREE.Vector3[] = [];
  for (let i = 0; i < count; i += 1) {
    const phi = Math.acos(1 - (2 * (i + 0.5)) / count);
    const theta = Math.PI * (1 + Math.sqrt(5)) * i;
    directions.push(
      new THREE.Vector3(Math.sin(phi) * Math.cos(theta), Math.cos(phi), Math.sin(phi) * Math.sin(theta)),
    );
  }
  return directions;
}

/**
 * A single merged `LineSegments` (one `BufferGeometry`, one draw call)
 * bridging the point cloud's outer layer and the shield outline with a
 * small, fixed number of paths (2-4). The dash pattern only flows during
 * the "submitting" phase, standing in for retrieval-in-progress; every
 * other phase renders the same static dashed lines at a phase-appropriate
 * opacity. Renamed from the retired `NeuralPaths.tsx`; same dash-offset
 * technique (manual `lineDistance` write instead of `dashOffset`, which
 * `LineDashedMaterial` in the installed `three` version does not expose).
 */
export function NeuralConnections({ phase }: NeuralConnectionsProps) {
  const lineRef = useRef<THREE.LineSegments>(null);
  const materialRef = useRef<THREE.LineDashedMaterial>(null);
  const baseDistancesRef = useRef<Float32Array | null>(null);

  const geometry = useMemo(() => {
    const positions: number[] = [];
    evenlySpreadDirections(PATH_COUNT).forEach((direction) => {
      const from = direction.clone().multiplyScalar(CORE_ANCHOR_RADIUS);
      const to = direction.clone().multiplyScalar(OUTER_ANCHOR_RADIUS);
      positions.push(from.x, from.y, from.z, to.x, to.y, to.z);
    });
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    return geom;
  }, []);

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

  useEffect(() => {
    const material = materialRef.current;
    if (!material) {
      return;
    }
    material.color.set(LIVING_CORE_PHASE_COLOR[phase]);
  }, [phase]);

  useFrame(({ clock }) => {
    const line = lineRef.current;
    const material = materialRef.current;
    const baseDistances = baseDistancesRef.current;
    if (!line || !material) {
      return;
    }

    const lineDistance = line.geometry.getAttribute("lineDistance") as
      | THREE.BufferAttribute
      | undefined;

    if (lineDistance && baseDistances) {
      const array = lineDistance.array as Float32Array;
      const flowOffset = phase === "submitting" ? clock.getElapsedTime() * 1.6 : 0;
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

    if (phase === "submitting") {
      material.opacity = 0.85;
    } else if (phase === "dormant") {
      material.opacity = 0.08;
    } else {
      material.opacity = 0.32;
    }
  });

  return (
    <lineSegments ref={lineRef} geometry={geometry} frustumCulled={false} renderOrder={1}>
      <lineDashedMaterial
        ref={materialRef}
        transparent
        depthWrite={false}
        dashSize={0.14}
        gapSize={0.09}
        opacity={0.32}
        toneMapped={false}
      />
    </lineSegments>
  );
}
