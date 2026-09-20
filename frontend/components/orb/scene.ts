import * as THREE from "three";

/**
 * The audio-reactive orb, ported from openclaw-jarvis-ui/src/core/scene.js.
 *
 * Differences from the original, all of them forced by React:
 *  - State lives in the closure rather than module scope, so a double-mount
 *    under Strict Mode can't have two scenes fighting over the same variables.
 *  - Nothing touches `window` until createOrbScene() runs.
 *  - Agent state arrives through method calls instead of window CustomEvents.
 *  - dispose() releases the WebGL context; without it every hot reload leaks
 *    one and the browser cuts you off after about sixteen.
 *
 * OrbitControls is intentionally absent: the original disabled rotate, pan and
 * zoom on it, so it did nothing but cost bytes.
 */

export type OrbAgentState = "idle" | "thinking" | "responding";

export interface OrbScene {
  /** Call once per frame. `audioLevel` is roughly 0..1. */
  animate(audioLevel: number, rotationSpeed: number, audioReactivity: number): void;
  setAgentState(state: OrbAgentState): void;
  /** 0..1 text-streaming speed; only meaningful while responding. */
  setStreamIntensity(value: number): void;
  setDistortion(value: number): void;
  setResolution(value: number): void;
  /** Pulls the camera in while the agent speaks. */
  setZoomed(zoomed: boolean): void;
  /** Re-reads the CSS custom properties after a hue change. */
  refreshTheme(): void;
  resize(): void;
  getOrbScreenPosition(): { x: number; y: number };
  dispose(): void;
}

const SIMPLEX_NOISE_GLSL = /* glsl */ `
  vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
  vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

  float snoise(vec3 v) {
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i  = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute(permute(permute(
            i.z + vec4(0.0, i1.z, i2.z, 1.0))
          + i.y + vec4(0.0, i1.y, i2.y, 1.0))
          + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ *ns.x + ns.yyyy;
    vec4 y = y_ *ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }
`;

const ORB_RADIUS = 2;

type ThemeColors = { primary: number; secondary: number; tertiary: number };

function readThemeColors(): ThemeColors {
  const fallback: ThemeColors = {
    primary: 0x4281ff,
    secondary: 0x2e5fc2,
    tertiary: 0xadc9ff,
  };
  if (typeof window === "undefined") return fallback;

  const style = getComputedStyle(document.documentElement);
  const parse = (name: string, fb: number) => {
    const raw = style.getPropertyValue(name).trim();
    if (!raw) return fb;
    try {
      return new THREE.Color(raw).getHex();
    } catch {
      return fb;
    }
  };

  return {
    primary: parse("--accent-primary", fallback.primary),
    secondary: parse("--accent-secondary", fallback.secondary),
    tertiary: parse("--accent-tertiary", fallback.tertiary),
  };
}

export function createOrbScene(container: HTMLElement): OrbScene {
  const isMobile = () => window.innerWidth <= 768;

  let themeColors = readThemeColors();

  let distortionAmount = 1;
  let resolution = 32;

  // Agent-state drive. `agentActivity` is a discrete 0/1/2; the smoothed value
  // is what actually reaches the shaders.
  let agentActivity = 0;
  let agentActivitySmooth = 0;
  let agentStateStartTime = performance.now();
  let streamIntensity = 0;
  let streamIntensitySmooth = 0;
  let doneBloom = 0;

  const clock = new THREE.Clock();

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x070a10, 0.05);

  const camera = new THREE.PerspectiveCamera(
    60,
    container.clientWidth / container.clientHeight,
    0.1,
    1000,
  );

  const defaultCamera = new THREE.Vector3(0, isMobile() ? 1.2 : 0, isMobile() ? 14 : 10);
  const zoomedCamera = new THREE.Vector3(0, 0, 8.5);
  let cameraTarget = defaultCamera.clone();
  camera.position.copy(defaultCamera);

  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
    stencil: false,
  });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setClearColor(0x000000, 0);
  // Capped at 2: the shaders are fill-rate heavy and 3x on a phone tanks it.
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0x404040, 1.5));
  const directional = new THREE.DirectionalLight(0xffffff, 1.5);
  directional.position.set(1, 1, 1);
  scene.add(directional);

  const pointLight1 = new THREE.PointLight(themeColors.primary, 1, 10);
  pointLight1.position.set(2, 2, 2);
  scene.add(pointLight1);
  const pointLight2 = new THREE.PointLight(themeColors.secondary, 1, 10);
  pointLight2.position.set(-2, -2, -2);
  scene.add(pointLight2);

  // ── Orb ──────────────────────────────────────────────────────────────

  let orb: THREE.Group;
  let outerMaterial: THREE.ShaderMaterial;
  let glowMaterial: THREE.ShaderMaterial;
  let outerGeometry: THREE.IcosahedronGeometry;
  let glowGeometry: THREE.SphereGeometry;

  function buildOrb() {
    if (orb) {
      scene.remove(orb);
      outerGeometry.dispose();
      glowGeometry.dispose();
      outerMaterial.dispose();
      glowMaterial.dispose();
    }

    orb = new THREE.Group();

    outerGeometry = new THREE.IcosahedronGeometry(
      ORB_RADIUS,
      Math.max(1, Math.floor(resolution / 8)),
    );
    outerMaterial = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        color: { value: new THREE.Color(themeColors.primary) },
        audioLevel: { value: 0 },
        distortion: { value: distortionAmount },
        agentActivity: { value: 0 },
      },
      vertexShader: /* glsl */ `
        uniform float time;
        uniform float audioLevel;
        uniform float distortion;
        uniform float agentActivity;
        varying vec3 vNormal;
        varying vec3 vPosition;

        ${SIMPLEX_NOISE_GLSL}

        void main() {
          vNormal = normalize(normalMatrix * normal);
          float slowTime = time * (0.3 + agentActivity * 0.35);
          vec3 pos = position;
          float noise = snoise(vec3(position.x * 0.5, position.y * 0.5, position.z * 0.5 + slowTime));
          pos += normal * noise * 0.2 * distortion * (1.0 + audioLevel * 1.1 + agentActivity * 0.25);
          vPosition = pos;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: /* glsl */ `
        uniform float time;
        uniform vec3 color;
        uniform float audioLevel;
        uniform float agentActivity;
        varying vec3 vNormal;
        varying vec3 vPosition;
        void main() {
          vec3 viewDirection = normalize(cameraPosition - vPosition);
          float fresnel = 1.0 - max(0.0, dot(viewDirection, vNormal));
          fresnel = pow(fresnel, 2.0 + audioLevel * 2.0);
          float pulse = 0.8 + 0.2 * sin(time * (2.0 + agentActivity));
          // Lifted off pure fresnel so the wireframe stays legible across the
          // face of the orb instead of going black toward the centre.
          float body = 0.25 + fresnel * 0.75;
          vec3 finalColor = color * body * pulse * (1.0 + audioLevel * 0.8 + agentActivity * 0.25);
          float alpha = body * (0.8 - audioLevel * 0.15);
          gl_FragColor = vec4(finalColor, alpha);
        }
      `,
      wireframe: true,
      transparent: true,
    });
    orb.add(new THREE.Mesh(outerGeometry, outerMaterial));

    glowGeometry = new THREE.SphereGeometry(ORB_RADIUS * 1.35, 48, 48);
    glowMaterial = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        color: { value: new THREE.Color(themeColors.primary) },
        audioLevel: { value: 0 },
        agentActivity: { value: 0 },
      },
      vertexShader: /* glsl */ `
        varying vec3 vNormal;
        varying vec3 vPosition;
        uniform float audioLevel;
        uniform float agentActivity;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          vPosition = position * (1.0 + audioLevel * 0.2 + agentActivity * 0.03);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(vPosition, 1.0);
        }
      `,
      fragmentShader: /* glsl */ `
        varying vec3 vNormal;
        varying vec3 vPosition;
        uniform vec3 color;
        uniform float time;
        uniform float audioLevel;
        uniform float agentActivity;
        void main() {
          vec3 viewDirection = normalize(cameraPosition - vPosition);
          // abs() because this shell renders BackSide: its normals point away
          // from the camera, so an unsigned dot would clamp to 0 everywhere and
          // light the whole disc uniformly. abs() gives 1 facing the camera and
          // 0 at the silhouette, so the inverse is a true rim.
          float rim = 1.0 - abs(dot(viewDirection, vNormal));
          rim = pow(rim, 3.5);
          float pulse = 0.5 + 0.5 * sin(time * 2.0);
          float audioFactor = 1.0 + audioLevel * 1.4 + agentActivity * 0.3;
          vec3 finalColor = color * rim * (0.8 + 0.2 * pulse) * audioFactor;
          float alpha = rim * 0.55 * audioFactor;
          gl_FragColor = vec4(finalColor, alpha);
        }
      `,
      transparent: true,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    orb.add(new THREE.Mesh(glowGeometry, glowMaterial));

    scene.add(orb);
  }

  // ── Background particles ─────────────────────────────────────────────

  let particles: THREE.Points;
  let particlesGeometry: THREE.BufferGeometry;
  let particlesMaterial: THREE.ShaderMaterial;

  function buildParticles() {
    if (particles) {
      scene.remove(particles);
      particlesGeometry.dispose();
      particlesMaterial.dispose();
    }

    const count = isMobile() ? 1000 : 3000;
    particlesGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);

    const palette = [
      new THREE.Color(themeColors.primary),
      new THREE.Color(themeColors.secondary),
      new THREE.Color(themeColors.tertiary),
    ];

    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 100;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 100;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 100;
      const color = palette[Math.floor(Math.random() * palette.length)];
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
      sizes[i] = 0.05;
    }

    particlesGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    particlesGeometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    particlesGeometry.setAttribute("size", new THREE.BufferAttribute(sizes, 1));

    particlesMaterial = new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 } },
      vertexShader: /* glsl */ `
        attribute float size;
        varying vec3 vColor;
        uniform float time;
        void main() {
          vColor = color;
          vec3 pos = position;
          pos.x += sin(time * 0.1 + position.z * 0.2) * 0.05;
          pos.y += cos(time * 0.1 + position.x * 0.2) * 0.05;
          pos.z += sin(time * 0.1 + position.y * 0.2) * 0.05;
          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          gl_PointSize = size * (300.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: /* glsl */ `
        varying vec3 vColor;
        void main() {
          float r = distance(gl_PointCoord, vec2(0.5, 0.5));
          if (r > 0.5) discard;
          float glow = 1.0 - (r * 2.0);
          glow = pow(glow, 2.0);
          gl_FragColor = vec4(vColor, glow);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      vertexColors: true,
    });

    particles = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particles);
  }

  buildOrb();
  buildParticles();

  // ── Frame update ─────────────────────────────────────────────────────

  function updateAgentActivity(time: number) {
    const elapsed = (performance.now() - agentStateStartTime) / 1000;
    let target = 0;

    if (agentActivity === 1) {
      // Thinking: ramps over ~10s, with layered sines for an irregular,
      // hesitant flicker rather than a clean pulse.
      const ramp = 0.5 + Math.min(elapsed / 10, 1) * 1.5;
      const jitter =
        Math.sin(elapsed * 2.3) * 0.12 +
        Math.sin(elapsed * 5.7) * 0.08 +
        Math.sin(elapsed * 11.3) * 0.04;
      target = ramp + jitter;
    } else if (agentActivity === 2) {
      streamIntensitySmooth += (streamIntensity - streamIntensitySmooth) * 0.1;
      target = 0.8 + streamIntensitySmooth * 1.5 + Math.sin(time * 1.2) * 0.1;
    }

    if (doneBloom > 0.01) {
      target += doneBloom * 2.5;
      doneBloom *= 0.95;
    } else {
      doneBloom = 0;
    }

    // Slower decay back to idle reads as settling rather than snapping.
    const smoothSpeed = agentActivity === 0 ? 0.02 : 0.06;
    agentActivitySmooth += (target - agentActivitySmooth) * smoothSpeed;
  }

  let disposed = false;

  return {
    animate(rawAudioLevel, rotationSpeed, audioReactivity) {
      if (disposed) return;
      const time = clock.getElapsedTime();
      // Clamped because the shaders are calibrated for 0..1; a loud spike past
      // that blows the glow out into a solid disc.
      const audioLevel = Math.min(1, Math.max(0, rawAudioLevel || 0));

      updateAgentActivity(time);

      camera.position.lerp(cameraTarget, 0.04);
      camera.lookAt(0, 0, 0);

      outerMaterial.uniforms.time.value = time;
      outerMaterial.uniforms.audioLevel.value = audioLevel;
      outerMaterial.uniforms.distortion.value = distortionAmount;
      outerMaterial.uniforms.agentActivity.value = agentActivitySmooth;

      glowMaterial.uniforms.time.value = time;
      glowMaterial.uniforms.audioLevel.value = audioLevel;
      glowMaterial.uniforms.agentActivity.value = agentActivitySmooth;

      particlesMaterial.uniforms.time.value = time;

      const audioRotation = 1 + audioLevel * audioReactivity;
      orb.rotation.y += 0.005 * rotationSpeed * audioRotation;
      orb.rotation.z += 0.002 * rotationSpeed * audioRotation;

      renderer.render(scene, camera);
    },

    setAgentState(state) {
      const next = state === "thinking" ? 1 : state === "responding" ? 2 : 0;
      if (next === agentActivity) return;
      // Leaving a response earns a brief bloom.
      if (next === 0 && agentActivity === 2) doneBloom = 1;
      agentActivity = next;
      agentStateStartTime = performance.now();
    },

    setStreamIntensity(value) {
      streamIntensity = value;
    },

    setDistortion(value) {
      distortionAmount = value;
    },

    setResolution(value) {
      if (value === resolution) return;
      resolution = value;
      buildOrb();
    },

    setZoomed(zoomed) {
      cameraTarget = zoomed ? zoomedCamera.clone() : defaultCamera.clone();
    },

    refreshTheme() {
      themeColors = readThemeColors();
      pointLight1.color.setHex(themeColors.primary);
      pointLight2.color.setHex(themeColors.secondary);
      outerMaterial.uniforms.color.value.setHex(themeColors.primary);
      glowMaterial.uniforms.color.value.setHex(themeColors.primary);
      buildParticles();
    },

    resize() {
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w === 0 || h === 0) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);

      defaultCamera.set(0, isMobile() ? 1.2 : 0, isMobile() ? 14 : 10);
      if (cameraTarget.z !== zoomedCamera.z) cameraTarget = defaultCamera.clone();
    },

    getOrbScreenPosition() {
      const pos = orb.position.clone().project(camera);
      const rect = container.getBoundingClientRect();
      return {
        x: (pos.x * 0.5 + 0.5) * rect.width,
        y: (-pos.y * 0.5 + 0.5) * rect.height,
      };
    },

    dispose() {
      disposed = true;
      outerGeometry.dispose();
      glowGeometry.dispose();
      outerMaterial.dispose();
      glowMaterial.dispose();
      particlesGeometry.dispose();
      particlesMaterial.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    },
  };
}
