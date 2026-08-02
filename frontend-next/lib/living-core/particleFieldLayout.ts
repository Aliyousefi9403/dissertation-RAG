import { LAYER_COUNT, LAYER_RADII, LAYER_RATIOS } from "@/lib/living-core/particleBudget";

export interface ParticleFieldLayout {
  /** Rest position (x, y, z) per particle, world units. Length is
   * `count * 3`. Every frame, `IntelligentParticleField`'s shader
   * recomputes an actual on-screen position from this rest position plus
   * curl-noise turbulence, breathing, and center-attraction — this array
   * itself never changes after layout. */
  positions: Float32Array;
  /** Per-particle random phase in [0, 1), used by the shader to
   * desynchronize breathing/turbulence so the field reads as one organic
   * body rather than particles moving in lockstep. Same indexing as
   * `positions`. */
  seeds: Float32Array;
  count: number;
}

/**
 * Deterministic, dependency-free PRNG (mulberry32) — a fixed seed keeps the
 * particle field's shape stable across re-renders/hot reloads instead of
 * reshuffling every time `buildParticleFieldLayout` happens to re-run for
 * the same `count`.
 */
function mulberry32(seed: number): () => number {
  let state = seed >>> 0;
  return function next() {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const LAYOUT_SEED = 0x5eed1234;

/**
 * Builds `count` particles spread across `LAYER_COUNT` concentric shells.
 * Within each shell, particles are placed with a Fibonacci-sphere spiral
 * (even angular coverage, no pole clustering, cheap and deterministic) with
 * a small per-particle radius jitter for an organic, non-uniform-crystal
 * look. The whole cloud is flattened slightly along y and z so it reads as
 * a volumetric body rather than a perfect sphere.
 */
export function buildParticleFieldLayout(count: number): ParticleFieldLayout {
  const totalCount = Math.max(0, Math.floor(count));
  const positions = new Float32Array(totalCount * 3);
  const seeds = new Float32Array(totalCount);
  const random = mulberry32(LAYOUT_SEED);

  let written = 0;
  for (let layer = 0; layer < LAYER_COUNT; layer += 1) {
    const isLastLayer = layer === LAYER_COUNT - 1;
    const layerCount = isLastLayer
      ? totalCount - written
      : Math.round(totalCount * LAYER_RATIOS[layer]);
    const radius = LAYER_RADII[layer] ?? LAYER_RADII[LAYER_RADII.length - 1];

    for (let i = 0; i < layerCount && written < totalCount; i += 1, written += 1) {
      const t = (i + 0.5) / Math.max(1, layerCount);
      const phi = Math.acos(1 - 2 * t);
      const theta = Math.PI * (1 + Math.sqrt(5)) * i;
      const jitter = 0.85 + random() * 0.3;
      const r = radius * jitter;

      const index = written * 3;
      positions[index] = Math.sin(phi) * Math.cos(theta) * r;
      positions[index + 1] = Math.cos(phi) * r * 0.92;
      positions[index + 2] = Math.sin(phi) * Math.sin(theta) * r * 0.85;
      seeds[written] = random();
    }
  }

  return { positions, seeds, count: totalCount };
}

export interface ParticleFieldConnections {
  /** Two vertices (this endpoint) per connection: rest position. */
  positions: Float32Array;
  seeds: Float32Array;
  /** Same length as `positions`/`seeds` — the *paired* endpoint's rest
   * position/seed, duplicated onto both of a segment's vertices so the
   * connection-lines vertex shader can independently recompute both ends'
   * live (curl-noise-displaced) position and derive their live distance,
   * entirely on the GPU, with no per-frame JS. */
  otherPositions: Float32Array;
  otherSeeds: Float32Array;
  /** Live distance beyond which a connection's shader fades to fully
   * transparent — a little past `MAX_CONNECTION_DISTANCE` since curl-noise
   * turbulence and breathing move particles beyond their rest spacing. */
  maxDistance: number;
}

const MAX_CONNECTION_DISTANCE = 0.25;
const MAX_HUB_COUNT = 1400;
const MAX_CONNECTIONS = 2200;

/**
 * Builds a small, capped set of "neural web" line segments between nearby
 * particles, using a spatial hash over an evenly-strided subset of the full
 * field — not all-pairs across the full 15k-30k particle count, which would
 * be O(n^2) and far too costly to build (or hold in one `BufferGeometry`)
 * on every device-tier change. The subset is representative of the whole
 * field's shape (evenly strided across the layout's construction order, not
 * clustered in one region), so the connections still read as spanning the
 * entire cloud.
 */
export function buildParticleConnections(layout: ParticleFieldLayout): ParticleFieldConnections {
  const { positions, seeds, count } = layout;
  const hubCount = Math.min(count, MAX_HUB_COUNT);
  const stride = Math.max(1, Math.floor(count / Math.max(1, hubCount)));

  const hubIndices: number[] = [];
  for (let i = 0; i < count && hubIndices.length < hubCount; i += stride) {
    hubIndices.push(i);
  }

  const cellSize = MAX_CONNECTION_DISTANCE;
  const grid = new Map<string, number[]>();
  const cellKey = (x: number, y: number, z: number) =>
    `${Math.floor(x / cellSize)}:${Math.floor(y / cellSize)}:${Math.floor(z / cellSize)}`;

  for (const particleIndex of hubIndices) {
    const base = particleIndex * 3;
    const key = cellKey(positions[base], positions[base + 1], positions[base + 2]);
    const bucket = grid.get(key);
    if (bucket) {
      bucket.push(particleIndex);
    } else {
      grid.set(key, [particleIndex]);
    }
  }

  const linePositions: number[] = [];
  const lineSeeds: number[] = [];
  const otherPositions: number[] = [];
  const otherSeeds: number[] = [];
  const seenPairs = new Set<string>();
  const maxDistanceSq = MAX_CONNECTION_DISTANCE * MAX_CONNECTION_DISTANCE;

  outer: for (const particleIndex of hubIndices) {
    const base = particleIndex * 3;
    const px = positions[base];
    const py = positions[base + 1];
    const pz = positions[base + 2];
    const cx = Math.floor(px / cellSize);
    const cy = Math.floor(py / cellSize);
    const cz = Math.floor(pz / cellSize);

    for (let dx = -1; dx <= 1; dx += 1) {
      for (let dy = -1; dy <= 1; dy += 1) {
        for (let dz = -1; dz <= 1; dz += 1) {
          const neighbors = grid.get(`${cx + dx}:${cy + dy}:${cz + dz}`);
          if (!neighbors) {
            continue;
          }
          for (const neighborIndex of neighbors) {
            if (neighborIndex <= particleIndex) {
              continue;
            }
            const pairKey = `${particleIndex}:${neighborIndex}`;
            if (seenPairs.has(pairKey)) {
              continue;
            }

            const nBase = neighborIndex * 3;
            const ddx = positions[nBase] - px;
            const ddy = positions[nBase + 1] - py;
            const ddz = positions[nBase + 2] - pz;
            const distSq = ddx * ddx + ddy * ddy + ddz * ddz;
            if (distSq > maxDistanceSq) {
              continue;
            }

            seenPairs.add(pairKey);
            linePositions.push(px, py, pz, positions[nBase], positions[nBase + 1], positions[nBase + 2]);
            lineSeeds.push(seeds[particleIndex], seeds[neighborIndex]);
            otherPositions.push(
              positions[nBase],
              positions[nBase + 1],
              positions[nBase + 2],
              px,
              py,
              pz,
            );
            otherSeeds.push(seeds[neighborIndex], seeds[particleIndex]);

            if (seenPairs.size >= MAX_CONNECTIONS) {
              break outer;
            }
          }
        }
      }
    }
  }

  return {
    positions: Float32Array.from(linePositions),
    seeds: Float32Array.from(lineSeeds),
    otherPositions: Float32Array.from(otherPositions),
    otherSeeds: Float32Array.from(otherSeeds),
    maxDistance: MAX_CONNECTION_DISTANCE * 1.6,
  };
}
