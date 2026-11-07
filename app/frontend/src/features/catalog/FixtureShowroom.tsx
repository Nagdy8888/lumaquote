import { useEffect, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { View } from "@react-three/drei";
import {
  AdditiveBlending,
  Color,
  type Group,
  type MeshBasicMaterial,
  type MeshStandardMaterial,
  type PointLight,
  type SpriteMaterial,
} from "three";
import {
  glowTexture,
  ignition,
  studioEnvironment,
  useScenePlayback,
} from "@/features/showcase/sceneKit";
import { FAMILIES, familyOf } from "./fixtureModels";

/** Background of every fixture tile; `.catalog-product-visual` uses the same value so tiles merge. */
const TILE_COLOUR = "#232a28";

/**
 * One product tile's scene: environment, lights, the family model and its glow.
 * Inputs: `family` SKU prefix, `index` (staggers ignition), `active` (card hovered or focused, which
 * brightens the lamp and turns it to face the viewer). Side effects: sets the View scene's
 * environment once; all motion mutates three.js objects in useFrame, never React state.
 */
function FixtureStage({
  family,
  index,
  active,
}: {
  family: string;
  index: number;
  active: boolean;
}) {
  const spec = FAMILIES[familyOf(family)];
  const scene = useThree((state) => state.scene);
  const gl = useThree((state) => state.gl);
  const turntable = useRef<Group>(null);
  const lens = useRef<MeshStandardMaterial>(null);
  const light = useRef<PointLight>(null);
  const halo = useRef<SpriteMaterial>(null);
  const pool = useRef<MeshBasicMaterial>(null);
  const level = useRef(0.85);
  const phase = (index * 1.7) % (Math.PI * 2);
  useEffect(
    /** Share one prefiltered studio map across every tile for brass reflections. */
    function applyEnvironment() {
      scene.environment = studioEnvironment(gl);
      scene.environmentIntensity = 0.55;
    },
    [scene, gl],
  );
  useFrame(
    /** Ignite once, idle-sway, and ease toward the hovered state. */
    function animate(state, delta) {
      const time = state.clock.elapsedTime;
      const ease = 1 - Math.exp(-delta * 5);
      level.current += ((active ? 1.45 : 0.85) - level.current) * ease;
      const glow = ignition(time, index % 9, 0.3, 0.09) * level.current;
      if (lens.current) lens.current.emissiveIntensity = 0.1 + glow * 2.4;
      if (light.current) light.current.intensity = glow * 3.5;
      if (halo.current) halo.current.opacity = glow * 0.5;
      if (pool.current) pool.current.opacity = glow * 0.28;
      const group = turntable.current;
      if (!group) return;
      const yaw = active ? 0 : Math.sin(time * 0.32 + phase) * 0.55;
      group.rotation.y += (yaw - group.rotation.y) * ease;
      group.position.y = Math.sin(time * 0.75 + phase) * 0.035;
    },
  );
  return (
    <>
      <color attach="background" args={[TILE_COLOUR]} />
      <ambientLight intensity={0.35} />
      <directionalLight position={[2.5, 3, 4]} intensity={1.3} />
      <directionalLight
        position={[-3, 1, -2]}
        intensity={0.5}
        color="#9fb7c9"
      />
      <group ref={turntable}>
        <group rotation={spec.tilt}>
          <spec.Model lens={lens} />
        </group>
        <pointLight
          ref={light}
          position={spec.glow}
          color={spec.colour}
          distance={4}
          decay={1.6}
        />
        <sprite position={spec.glow} scale={[spec.halo, spec.halo, 1]}>
          <spriteMaterial
            ref={halo}
            map={glowTexture()}
            color={new Color(spec.colour)}
            transparent
            opacity={0}
            blending={AdditiveBlending}
            depthWrite={false}
          />
        </sprite>
      </group>
      <mesh
        position={[0, -0.95, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
        scale={[2.6, 1.6, 1]}
      >
        <planeGeometry />
        <meshBasicMaterial
          ref={pool}
          map={glowTexture()}
          color={spec.colour}
          transparent
          opacity={0}
          blending={AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
    </>
  );
}

/**
 * DOM slot for one product tile. drei View tunnels the scene into the shared FixtureCanvas, which
 * draws it into this element's rectangle; without that canvas it renders an empty div, so the CSS
 * fixture underneath stays visible. Decorative: the card text carries all product information.
 */
export function FixtureView({
  family,
  index,
  active,
}: {
  family: string;
  index: number;
  active: boolean;
}) {
  return (
    <View className="fixture-view">
      <FixtureStage family={family} index={index} active={active} />
    </View>
  );
}

/**
 * The single WebGL canvas behind every catalog tile: fixed to the viewport, below the shell's
 * sticky bar and dialogs, never a pointer target. Output: null under reduced motion (no canvas).
 * `onReady` fires once the WebGL context exists so the page can restyle tiles for the dark stage;
 * if WebGL is unavailable it never fires and the static CSS fixtures stay. Rendering pauses while
 * the tab is hidden and while `paused` (the inspector dialog covers the page).
 */
export default function FixtureCanvas({
  onReady,
  paused = false,
}: {
  onReady: (ready: boolean) => void;
  paused?: boolean;
}) {
  const { ref, reduced, frameloop } = useScenePlayback<HTMLDivElement>();
  useEffect(
    /** Tell the page the stage is gone when this canvas unmounts. */
    function reportUnmount() {
      /** Report that the stage no longer exists, so tiles return to the static look. */
      return function cleanup() {
        onReady(false);
      };
    },
    [onReady],
  );
  if (reduced) return null;
  return (
    <div ref={ref} className="fixture-canvas" aria-hidden="true">
      <Canvas
        frameloop={paused ? "never" : frameloop}
        dpr={[1, 1.75]}
        camera={{ position: [0, 0.2, 3.3], fov: 34 }}
        onCreated={() => onReady(true)}
        fallback={null}
        style={{ pointerEvents: "none" }}
      >
        <View.Port />
      </Canvas>
    </div>
  );
}
