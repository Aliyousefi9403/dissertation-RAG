"use client";

import { useEffect, useMemo } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

interface BloomComposerProps {
  strength?: number;
  radius?: number;
  threshold?: number;
}

/**
 * Manual `EffectComposer` wiring using three's own bundled
 * `examples/jsm/postprocessing` passes (aliased via `three/addons/*`) --
 * no `@react-three/postprocessing`/`postprocessing` package, since neither
 * is an installed dependency and `three` already ships everything needed.
 *
 * Registering a `useFrame` callback at a positive render priority tells r3f
 * to skip its own default `gl.render(scene, camera)` for this canvas (see
 * https://r3f.docs.pmnd.rs/api/canvas#render-props), so this becomes the
 * only place the scene is actually drawn each invalidated frame, in both
 * "demand" and "always" frameloop modes.
 *
 * Threshold/strength/radius are tuned so only the particle field's
 * near-white cores (and any other saturated blue/white highlight) cross the
 * bloom threshold -- the dimmer retrieval/status UI elsewhere in the scene
 * stays essentially unaffected.
 */
export function BloomComposer({ strength = 0.85, radius = 0.55, threshold = 0.22 }: BloomComposerProps) {
  const { gl, scene, camera, size } = useThree();

  const composer = useMemo(() => {
    const instance = new EffectComposer(gl);
    instance.addPass(new RenderPass(scene, camera));
    instance.addPass(
      new UnrealBloomPass(new THREE.Vector2(size.width, size.height), strength, radius, threshold),
    );
    instance.addPass(new OutputPass());
    return instance;
    // Uniform/pass tuning is applied imperatively below (not re-created on
    // every prop change) -- only a renderer identity change warrants a
    // fresh composer + its render targets.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gl]);

  useEffect(() => {
    composer.setPixelRatio(gl.getPixelRatio());
    composer.setSize(size.width, size.height);
  }, [composer, gl, size]);

  useEffect(() => {
    const bloomPass = composer.passes.find(
      (pass): pass is UnrealBloomPass => pass instanceof UnrealBloomPass,
    );
    if (!bloomPass) {
      return;
    }
    bloomPass.strength = strength;
    bloomPass.radius = radius;
    bloomPass.threshold = threshold;
  }, [composer, strength, radius, threshold]);

  useEffect(() => () => composer.dispose(), [composer]);

  useFrame((_, delta) => {
    composer.render(delta);
  }, 1);

  return null;
}
