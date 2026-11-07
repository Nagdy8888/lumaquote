import { useMemo, useRef, type RefObject } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, Lightformer } from "@react-three/drei";
import {
  AdditiveBlending,
  BackSide,
  Color,
  type Group,
  type MeshStandardMaterial,
  type Sprite,
} from "three";
import {
  LIGHT_COLOURS,
  glowTexture,
  ignition,
  useScenePlayback,
} from "./sceneKit";

/** Ceiling height the cords hang from; above the visible frame so cords enter from the top edge. */
const CEILING = 4.2;

type PendantSpec = { x: number; z: number; drop: number; phase: number };

/**
 * Lay out a fixed, deterministic cluster of pendants in the upper part of the frame.
 * Pure: the same `count` always gives the same layout, so screenshots and recordings repeat.
 * Bulbs stay above y≈0.2 to leave the lower frame free for the headline.
 */
function layout(count: number): PendantSpec[] {
  const specs: PendantSpec[] = [];
  for (let i = 0; i < count; i += 1) {
    const golden = (i * 0.618034) % 1;
    const row = i % 3;
    specs.push({
      x: -2.3 + golden * 5.1,
      z: -2.8 + row * 1.35 + ((i * 0.37) % 0.6),
      drop: 2.1 + ((i * 0.53) % 1) * 1.9,
      phase: i * 1.7,
    });
  }
  return specs.sort((a, b) => a.x - b.x);
}

/**
 * Animate every pendant in one frame callback: sway, staggered ignition and pointer glow.
 * Input: layout `specs`. Side effects: mutates only Three.js objects owned by this component; no
 * React state changes per frame.
 */
function Pendants({ specs }: { specs: PendantSpec[] }) {
  const swings = useRef<(Group | null)[]>([]);
  const halos = useRef<(Sprite | null)[]>([]);
  const glows = useRef<(MeshStandardMaterial | null)[]>([]);
  const boosts = useRef(specs.map(() => 0));
  const lit = useMemo(() => new Color(LIGHT_COLOURS.warm), []);
  const dark = useMemo(() => new Color("#2b2a26"), []);
  const texture = useMemo(() => glowTexture(), []);
  useFrame(
    /** Advance the shared animation for all pendants from the canvas clock and pointer. */
    function animate({ clock, pointer, viewport }) {
      const time = clock.elapsedTime;
      specs.forEach((spec, index) => {
        const swing = swings.current[index];
        const halo = halos.current[index];
        const glow = glows.current[index];
        if (!swing || !halo || !glow) return;
        const on = ignition(time, index, 0.5, 0.11);
        swing.rotation.z = Math.sin(time * 0.55 + spec.phase) * 0.035;
        swing.rotation.x = Math.cos(time * 0.42 + spec.phase) * 0.025;
        const pointerX = (pointer.x * viewport.width) / 2;
        const pointerY = (pointer.y * viewport.height) / 2;
        const bulbY = CEILING - spec.drop;
        const distance = Math.hypot(pointerX - spec.x, pointerY - bulbY);
        const target = Math.max(0, 1 - distance / 1.6);
        boosts.current[index] += (target - boosts.current[index]) * 0.08;
        const boost = boosts.current[index];
        halo.material.opacity = on * (0.5 + 0.5 * boost);
        const size = (0.95 + 0.75 * boost) * (0.6 + 0.4 * on);
        halo.scale.set(size, size, 1);
        glow.emissive.copy(dark).lerp(lit, on);
        glow.emissiveIntensity = 1.2 + 1.6 * boost;
      });
    },
  );
  return (
    <>
      {specs.map((spec, index) => (
        <group key={index} position={[spec.x, CEILING, spec.z]}>
          <group
            ref={(node) => {
              swings.current[index] = node;
            }}
          >
            <mesh position={[0, -spec.drop / 2, 0]}>
              <cylinderGeometry args={[0.006, 0.006, spec.drop, 6]} />
              <meshStandardMaterial color="#141716" roughness={0.6} />
            </mesh>
            <group position={[0, -spec.drop, 0]}>
              <mesh>
                <sphereGeometry args={[0.24, 40, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
                <meshStandardMaterial
                  color="#c0906a"
                  metalness={0.85}
                  roughness={0.28}
                />
              </mesh>
              <mesh scale={0.985}>
                <sphereGeometry args={[0.24, 40, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
                <meshStandardMaterial
                  ref={(node) => {
                    glows.current[index] = node;
                  }}
                  side={BackSide}
                  color="#1d1c19"
                  emissive="#2b2a26"
                  emissiveIntensity={1.2}
                  roughness={0.9}
                />
              </mesh>
              <sprite
                ref={(node) => {
                  halos.current[index] = node;
                }}
                position={[0, -0.06, 0]}
              >
                <spriteMaterial
                  map={texture}
                  color={LIGHT_COLOURS.warm}
                  blending={AdditiveBlending}
                  transparent
                  opacity={0}
                  depthWrite={false}
                  fog={false}
                  toneMapped={false}
                />
              </sprite>
            </group>
          </group>
        </group>
      ))}
    </>
  );
}

/**
 * Decorative full-bleed field of brass pendant lights for the sign-in story panel.
 * The canvas is hidden from assistive technology; the panel's headline carries the meaning.
 * Bulbs ignite in a left-to-right wave on load, sway gently and brighten near the pointer.
 * Reduced motion renders nothing (the panel's static gradient remains). Off-screen or hidden tabs
 * stop rendering.
 */
export default function PendantField() {
  const { ref, reduced, frameloop } = useScenePlayback<HTMLDivElement>();
  const specs = useMemo(() => layout(15), []);
  if (reduced) return null;
  return (
    <div className="pendant-field" ref={ref} aria-hidden="true">
      <Canvas
        frameloop={frameloop}
        dpr={[1, 1.75]}
        camera={{ position: [0, 1.4, 7.2], fov: 42 }}
        gl={{ alpha: true, antialias: true }}
        eventSource={ref as RefObject<HTMLElement>}
        eventPrefix="client"
      >
        <fog attach="fog" args={["#202727", 6.5, 12]} />
        <ambientLight intensity={0.35} />
        <directionalLight position={[2, 3, 4]} intensity={0.9} color="#ffe2bf" />
        <Environment resolution={64} frames={1}>
          <Lightformer
            form="rect"
            intensity={2.2}
            color="#ffd7a8"
            position={[0, -3, 2]}
            scale={[10, 2, 1]}
          />
          <Lightformer
            form="rect"
            intensity={0.8}
            color="#9fb3ad"
            position={[-4, 2, -2]}
            scale={[3, 6, 1]}
          />
        </Environment>
        <Pendants specs={specs} />
      </Canvas>
    </div>
  );
}
