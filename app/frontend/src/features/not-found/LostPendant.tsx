import { useEffect, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  AdditiveBlending,
  DoubleSide,
  type Group,
  type MeshBasicMaterial,
  type MeshStandardMaterial,
  type PointLight,
  type SpriteMaterial,
} from "three";
import {
  glowTexture,
  LIGHT_COLOURS,
  studioEnvironment,
  useScenePlayback,
} from "@/features/showcase/sceneKit";

const CEILING = 2.4;
const DROP = 2.1;

/**
 * Brightness of a failing lamp at `time` seconds: mostly a low ember, with irregular sputters back
 * to full light. Pure and deterministic, so every visit flickers the same way.
 */
function sputter(time: number) {
  const wave =
    Math.sin(time * 13.1) +
    Math.sin(time * 7.3 + 1.2) +
    Math.sin(time * 2.9 + 0.4);
  if (wave > 1.5) return 1;
  if (wave > 1.1) return 0.55;
  return 0.14;
}

/** Give the scene the shared studio reflections so the painted dome reads as metal, not a hole. */
function Studio() {
  const scene = useThree((state) => state.scene);
  const gl = useThree((state) => state.gl);
  useEffect(
    /** Assign the cached environment once per renderer. */
    function applyEnvironment() {
      scene.environment = studioEnvironment(gl);
      scene.environmentIntensity = 0.4;
    },
    [scene, gl],
  );
  return null;
}

/** One pendant swinging from the ceiling with a bulb that keeps trying to come back on. */
function Pendant() {
  const swing = useRef<Group>(null);
  const bulb = useRef<MeshStandardMaterial>(null);
  const light = useRef<PointLight>(null);
  const halo = useRef<SpriteMaterial>(null);
  const pool = useRef<MeshBasicMaterial>(null);
  const poolMesh = useRef<Group>(null);
  const level = useRef(0);
  useFrame(
    /** Swing gently, sputter the bulb, and keep the floor pool under the lamp. */
    function animate(state, delta) {
      const time = state.clock.elapsedTime;
      const angle = Math.sin(time * 0.85) * 0.14;
      if (swing.current) swing.current.rotation.z = angle;
      level.current +=
        (sputter(time) - level.current) * Math.min(1, delta * 22);
      const glow = level.current;
      if (bulb.current) bulb.current.emissiveIntensity = 0.3 + glow * 3;
      if (light.current) light.current.intensity = glow * 14;
      if (halo.current) halo.current.opacity = glow * 0.85;
      if (pool.current) pool.current.opacity = 0.08 + glow * 0.4;
      if (poolMesh.current)
        poolMesh.current.position.x = Math.sin(angle) * (DROP + 1.2);
    },
  );
  return (
    <>
      <group ref={swing} position={[0, CEILING, 0]}>
        <mesh position={[0, -DROP / 2, 0]}>
          <cylinderGeometry args={[0.012, 0.012, DROP, 6]} />
          <meshStandardMaterial color="#1a1f1d" />
        </mesh>
        <group position={[0, -DROP, 0]}>
          <mesh position={[0, 0.06, 0]}>
            <cylinderGeometry args={[0.06, 0.08, 0.14, 24]} />
            <meshStandardMaterial
              color="#c9a46a"
              metalness={0.85}
              roughness={0.3}
            />
          </mesh>
          <mesh>
            <sphereGeometry
              args={[0.52, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]}
            />
            <meshStandardMaterial
              color="#4a5550"
              metalness={0.45}
              roughness={0.4}
              side={DoubleSide}
            />
          </mesh>
          <mesh position={[0, -0.08, 0]}>
            <sphereGeometry args={[0.16, 32, 16]} />
            <meshStandardMaterial
              ref={bulb}
              color="#fff4e2"
              emissive={LIGHT_COLOURS.warm}
              emissiveIntensity={0}
            />
          </mesh>
          <pointLight
            ref={light}
            position={[0, -0.25, 0]}
            color={LIGHT_COLOURS.warm}
            distance={7}
            decay={1.4}
          />
          <sprite position={[0, -0.12, 0.1]} scale={[2.4, 2.4, 1]}>
            <spriteMaterial
              ref={halo}
              map={glowTexture()}
              color={LIGHT_COLOURS.warm}
              transparent
              opacity={0}
              blending={AdditiveBlending}
              depthWrite={false}
            />
          </sprite>
        </group>
      </group>
      <group ref={poolMesh} position={[0, -1.25, 0]}>
        <mesh rotation={[-Math.PI / 2, 0, 0]} scale={[4.2, 2.6, 1]}>
          <planeGeometry />
          <meshBasicMaterial
            ref={pool}
            map={glowTexture()}
            color={LIGHT_COLOURS.warm}
            transparent
            opacity={0}
            blending={AdditiveBlending}
            depthWrite={false}
          />
        </mesh>
      </group>
    </>
  );
}

/**
 * Decorative 404 scene: a lone pendant whose bulb has nearly gone out. Output: a dark panel with
 * one canvas, or null under reduced motion (no canvas). Hidden from assistive technology; the page
 * text and buttons carry the message. Pauses off screen and in hidden tabs.
 */
export default function LostPendant() {
  const { ref, reduced, frameloop } = useScenePlayback<HTMLDivElement>();
  if (reduced) return null;
  return (
    <div ref={ref} className="lost-pendant" aria-hidden="true">
      <Canvas
        frameloop={frameloop}
        dpr={[1, 1.75]}
        camera={{ position: [0, 0.5, 4.4], fov: 40 }}
        fallback={null}
      >
        <color attach="background" args={["#202727"]} />
        <fog attach="fog" args={["#202727", 5, 10]} />
        <ambientLight intensity={0.3} />
        <directionalLight
          position={[2, 3, 4]}
          intensity={0.6}
          color="#d9e2ea"
        />
        <Studio />
        <Pendant />
      </Canvas>
    </div>
  );
}
