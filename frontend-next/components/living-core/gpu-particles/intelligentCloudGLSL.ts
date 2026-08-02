/**
 * Shared "where is this particle right now" function used verbatim by both
 * `IntelligentParticleField`'s point-cloud vertex shader and its
 * connection-line vertex shader, so the two draw calls can never visually
 * desync even though they're separate `BufferGeometry`s. DEPENDS ON
 * `curl3D` (see `noiseGLSL.ts`) being concatenated earlier in the final
 * shader source, and on each consuming shader declaring the uniforms
 * referenced below (`uTime`, `uCurlAmp`, `uCurlScale`, `uCurlSpeed`,
 * `uAttract`, `uBreatheAmp`, `uBreatheFreq`, `uDigestAmp`, `uDigestFreq`)
 * with matching names.
 *
 * Fully stateless: every frame recomputes a particle's live position from
 * scratch out of its fixed rest position + seed + the current time, so
 * there is no GPU ping-pong/feedback texture to maintain — the entire
 * "simulation" is this one pure function evaluated per-vertex.
 */
export const LIVE_POSITION_GLSL = /* glsl */ `
  uniform float uTime;
  uniform float uCurlAmp;
  uniform float uCurlScale;
  uniform float uCurlSpeed;
  uniform float uAttract;
  uniform float uBreatheAmp;
  uniform float uBreatheFreq;
  uniform float uDigestAmp;
  uniform float uDigestFreq;

  // Slow, constant breathing (uniform radial scale, phase-offset per
  // particle via seed) layered with a curl-noise turbulence field --
  // curl noise is divergence-free, so it swirls particles around rather
  // than ever draining them toward or exploding them away from a point.
  // The result is then gently pulled back toward its own rest radius
  // (never the world origin) so the field stays one coherent bounded
  // volume instead of diffusing apart under the turbulence -- "gentle
  // attraction toward the center" of the cloud's own layered shell, not a
  // collapse to a single point.
  //
  // uDigestAmp is a second, much larger radial pulse with NO per-particle
  // seed offset (unlike the idle breathe term above) -- every particle
  // contracts and expands in lockstep, so the whole field reads as one
  // coherent "open and close" gesture (eased in/out via uDigestAmp itself
  // ramping from 0, see IntelligentParticleField's useFrame) rather than
  // organic per-particle jitter. Zero whenever not submitting a question.
  vec3 livePosition(vec3 restPosition, float seed) {
    float breathe = 1.0
      + sin(uTime * uBreatheFreq + seed * 6.28318) * uBreatheAmp
      + sin(uTime * uDigestFreq) * uDigestAmp;
    vec3 base = restPosition * breathe;

    vec3 turbulence = curl3D(base * uCurlScale + vec3(0.0, 0.0, uTime * uCurlSpeed) + seed * 41.0) * uCurlAmp;
    vec3 wandered = base + turbulence;

    float baseLen = length(base);
    float wanderedLen = length(wandered);
    if (wanderedLen < 0.0001) {
      return wandered;
    }
    return mix(wandered, normalize(wandered) * baseLen, uAttract);
  }
`;
