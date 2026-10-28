"use client";

import { useEffect, useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

import { damp } from "@/lib/living-core/damp";

interface BloomComposerProps {
  strength?: number;
  radius?: number;
  threshold?: number;
}

// Response rate for easing toward a new strength/radius/threshold target.
const BLOOM_LAMBDA = 5;

/**
 * Manual `EffectComposer` wiring using three's own bundled `examples/jsm/postprocessing`
 * passes.
 */
export function BloomComposer({
  strength = 1.2,
  radius = 0.8,
  threshold = 0.2,
}: BloomComposerProps) {
  const { gl, scene, camera, size } = useThree();
  const currentRef = useRef({ strength, radius, threshold });

  const composer = useMemo(() => {
    const instance = new EffectComposer(gl);
    instance.addPass(new RenderPass(scene, camera));
    instance.addPass(
      new UnrealBloomPass(new THREE.Vector2(size.width, size.height), strength, radius, threshold),
    );
    instance.addPass(new OutputPass());
    return instance;
    // Uniform/pass tuning is damped toward the latest props every frame
    // below (not re-created on every prop change) -- only a renderer
    // identity change warrants a fresh composer + its render targets.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gl]);

  useEffect(() => {
    composer.setPixelRatio(gl.getPixelRatio());
    composer.setSize(size.width, size.height);
  }, [composer, gl, size]);

  useEffect(() => () => composer.dispose(), [composer]);

  useFrame((_, delta) => {
    const bloomPass = composer.passes.find(
      (pass): pass is UnrealBloomPass => pass instanceof UnrealBloomPass,
    );
    if (bloomPass) {
      const dt = Math.min(0.1, Math.max(0, delta));
      const current = currentRef.current;
      current.strength = damp(current.strength, strength, BLOOM_LAMBDA, dt);
      current.radius = damp(current.radius, radius, BLOOM_LAMBDA, dt);
      current.threshold = damp(current.threshold, threshold, BLOOM_LAMBDA, dt);
      bloomPass.strength = current.strength;
      bloomPass.radius = current.radius;
      bloomPass.threshold = current.threshold;
    }
    composer.render(delta);
  }, 1);

  return null;
}
