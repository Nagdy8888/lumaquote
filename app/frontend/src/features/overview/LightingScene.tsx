import { useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import {
  AdditiveBlending,
  CanvasTexture,
  Color,
  ConeGeometry,
  DoubleSide,
  Object3D,
  Vector3,
  type Group,
  type Mesh,
  type MeshBasicMaterial,
  type SpotLight,
  type Sprite,
} from "three";
import {
  LIGHT_COLOURS,
  glowTexture,
  ignition,
  useScenePlayback,
  type LightTemperature,
} from "@/features/showcase/sceneKit";
import { LightingFallback } from "./SceneBoundary";

/** Rail height, wall depth and floor level of the illustrative showroom, in scene units. */
const RAIL_Y = 1.35;
const WALL_Z = -1.7;
const FLOOR_Y = -1.15;
/** Base x positions of the three track heads and the wall points they wash. */
const HEADS = [-1.25, 0, 1.25];
/** Unit beam length the cone geometry is built at; each frame scales it to the real distance. */
const BEAM = 3;

/**
 * Build a soft beam cone with its apex at the origin pointing along +Z, so `lookAt` aims it.
 * Pure geometry factory; the caller owns disposal through React Three Fiber's primitive cleanup.
 */
function beamGeometry(radius: number) {
  const geometry = new ConeGeometry(radius, BEAM, 48, 1, true);
  geometry.translate(0, -BEAM / 2, 0);
  geometry.rotateX(-Math.PI / 2);
  return geometry;
}

let fade: CanvasTexture | null = null;

/** Return a cached vertical fade used as the beams' alpha map (bright at the lens, clear at the far end). */
function beamFade() {
  if (fade) return fade;
  const canvas = document.createElement("canvas");
  canvas.width = 4;
  canvas.height = 128;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("2D canvas unavailable for beam fade");
  const gradient = context.createLinearGradient(0, 0, 0, 128);
  gradient.addColorStop(0, "#fff");
  gradient.addColorStop(0.55, "#555");
  gradient.addColorStop(1, "#000");
  context.fillStyle = gradient;
  context.fillRect(0, 0, 4, 128);
  fade = new CanvasTexture(canvas);
  return fade;
}

type HeadParts = {
  head: Group | null;
  light: SpotLight | null;
  outer: Mesh | null;
  inner: Mesh | null;
  halo: Sprite | null;
  lens: MeshBasicMaterial | null;
  pool: Mesh | null;
};

/**
 * Three track heads that ignite in sequence, aim toward the pointer and cross-fade colour.
 * Input: `temperature`, the target display colour.
 * Side effects: mutates only the Three.js objects it renders, once per frame. No React state.
 */
function TrackHeads({ temperature }: { temperature: LightTemperature }) {
  const parts = useRef<HeadParts[]>(
    HEADS.map(() => ({
      head: null,
      light: null,
      outer: null,
      inner: null,
      halo: null,
      lens: null,
      pool: null,
    })),
  );
  const targets = useMemo(() => HEADS.map(() => new Object3D()), []);
  const outerGeometry = useMemo(() => beamGeometry(0.62), []);
  const innerGeometry = useMemo(() => beamGeometry(0.3), []);
  const alpha = useMemo(() => beamFade(), []);
  const halo = useMemo(() => glowTexture(), []);
  const colour = useMemo(() => new Color(LIGHT_COLOURS.warm), []);
  const goal = useMemo(() => new Color(), []);
  const aim = useMemo(() => new Vector3(), []);
  useFrame(
    /** Advance ignition, pointer aiming and the colour cross-fade for all three heads. */
    function animate({ clock, pointer }) {
      const time = clock.elapsedTime;
      goal.set(LIGHT_COLOURS[temperature]);
      colour.lerp(goal, 0.06);
      HEADS.forEach((x, index) => {
        const part = parts.current[index];
        const target = targets[index];
        if (!part.head || !part.light || !part.outer || !part.inner) return;
        if (!part.halo || !part.lens || !part.pool) return;
        const on = ignition(time, index, 0.6, 0.45);
        const sweep = Math.sin(time * 0.35 + index * 2.1) * 0.18;
        const desired = x * 1.3 + sweep + pointer.x * 0.9;
        target.position.x += (desired - target.position.x) * 0.05;
        target.position.y = -0.25 + pointer.y * 0.25;
        target.position.z = WALL_Z;
        target.updateMatrixWorld();
        part.head.lookAt(target.position);
        part.head.getWorldPosition(aim);
        part.outer.position.copy(aim);
        part.inner.position.copy(aim);
        part.outer.lookAt(target.position);
        part.inner.lookAt(target.position);
        const reach = aim.distanceTo(target.position) / BEAM;
        part.outer.scale.set(1, 1, reach * 1.25);
        part.inner.scale.set(1, 1, reach * 1.15);
        part.light.intensity = 46 * on;
        part.light.color.copy(colour);
        (part.outer.material as MeshBasicMaterial).color.copy(colour);
        (part.outer.material as MeshBasicMaterial).opacity = 0.07 * on;
        (part.inner.material as MeshBasicMaterial).color.copy(colour);
        (part.inner.material as MeshBasicMaterial).opacity = 0.1 * on;
        part.halo.material.color.copy(colour);
        part.halo.material.opacity = 0.9 * on;
        part.lens.color.copy(colour).multiplyScalar(0.25 + 0.75 * on);
        part.pool.position.x = target.position.x;
        (part.pool.material as MeshBasicMaterial).color.copy(colour);
        (part.pool.material as MeshBasicMaterial).opacity = 0.7 * on;
      });
    },
  );
  return (
    <>
      <mesh position={[0, RAIL_Y + 0.12, 0.25]}>
        <boxGeometry args={[4.2, 0.06, 0.07]} />
        <meshStandardMaterial color="#2c3230" metalness={0.7} roughness={0.35} />
      </mesh>
      {targets.map((target, index) => (
        <primitive key={`target-${index}`} object={target} />
      ))}
      {HEADS.map((x, index) => (
        <group key={x}>
          <mesh position={[x, RAIL_Y + 0.02, 0.25]}>
            <cylinderGeometry args={[0.025, 0.025, 0.2, 12]} />
            <meshStandardMaterial color="#2c3230" metalness={0.7} roughness={0.35} />
          </mesh>
          <group
            position={[x, RAIL_Y - 0.12, 0.25]}
            ref={(node) => {
              parts.current[index].head = node;
            }}
          >
            <mesh rotation={[Math.PI / 2, 0, 0]}>
              <cylinderGeometry args={[0.13, 0.15, 0.42, 40]} />
              <meshStandardMaterial color="#b98a69" metalness={0.75} roughness={0.3} />
            </mesh>
            <mesh position={[0, 0, 0.212]}>
              <circleGeometry args={[0.125, 40]} />
              <meshBasicMaterial
                ref={(node) => {
                  parts.current[index].lens = node;
                }}
                color={LIGHT_COLOURS.warm}
                toneMapped={false}
              />
            </mesh>
            <sprite
              position={[0, 0, 0.26]}
              scale={[0.9, 0.9, 1]}
              ref={(node) => {
                parts.current[index].halo = node;
              }}
            >
              <spriteMaterial
                map={halo}
                blending={AdditiveBlending}
                transparent
                opacity={0}
                depthWrite={false}
                toneMapped={false}
              />
            </sprite>
            <spotLight
              ref={(node) => {
                parts.current[index].light = node;
              }}
              target={targets[index]}
              position={[0, 0, 0.22]}
              angle={0.34}
              penumbra={0.38}
              decay={1.4}
              distance={10}
              intensity={0}
            />
          </group>
          <mesh
            rotation={[-Math.PI / 2, 0, 0]}
            position={[x, FLOOR_Y + 0.002, WALL_Z + 0.55]}
            scale={[2.4, 1.7, 1]}
            ref={(node) => {
              parts.current[index].pool = node;
            }}
          >
            <planeGeometry />
            <meshBasicMaterial
              map={halo}
              blending={AdditiveBlending}
              transparent
              opacity={0}
              depthWrite={false}
              toneMapped={false}
            />
          </mesh>
          {(["outer", "inner"] as const).map((layer) => (
            <mesh
              key={layer}
              geometry={layer === "outer" ? outerGeometry : innerGeometry}
              ref={(node) => {
                parts.current[index][layer] = node;
              }}
              raycast={() => null}
            >
              <meshBasicMaterial
                alphaMap={alpha}
                blending={AdditiveBlending}
                transparent
                opacity={0}
                depthWrite={false}
                side={DoubleSide}
                toneMapped={false}
              />
            </mesh>
          ))}
        </group>
      ))}
    </>
  );
}

/**
 * Back wall of narrow vertical flutes, so the beams draw scallops with texture.
 * One instanced mesh keeps it to a single draw call. Static: no per-frame work.
 */
function FlutedWall() {
  const count = 72;
  const width = 0.16;
  const flutes = useMemo(() => {
    const dummy = new Object3D();
    return Array.from({ length: count }, (_, index) => {
      dummy.position.set((index - count / 2) * (width + 0.02), 0.6, WALL_Z);
      dummy.updateMatrix();
      return dummy.matrix.clone();
    });
  }, []);
  return (
    <>
      <mesh position={[0, 0.6, WALL_Z - 0.04]}>
        <planeGeometry args={[16, 5]} />
        <meshStandardMaterial color="#232826" roughness={1} />
      </mesh>
      <instancedMesh
        args={[undefined, undefined, count]}
        ref={(node) => {
          if (!node) return;
          flutes.forEach((matrix, index) => node.setMatrixAt(index, matrix));
          node.instanceMatrix.needsUpdate = true;
        }}
      >
        <cylinderGeometry args={[width / 2, width / 2, 5, 16, 1, false, -Math.PI / 2, Math.PI]} />
        <meshStandardMaterial color="#5b5d55" roughness={0.78} />
      </instancedMesh>
    </>
  );
}

/**
 * Drift the camera slowly and follow the pointer a little, so the showroom reads as 3D.
 * Side effect: moves the default camera each frame.
 */
function CameraDrift() {
  useFrame(
    /** Ease the camera toward a slow orbit offset plus a small pointer parallax. */
    function drift({ camera, clock, pointer }) {
      const time = clock.elapsedTime;
      const x = Math.sin(time * 0.16) * 0.45 + pointer.x * 0.35;
      const y = 0.2 + Math.cos(time * 0.12) * 0.12 + pointer.y * 0.15;
      camera.position.x += (x - camera.position.x) * 0.04;
      camera.position.y += (y - camera.position.y) * 0.04;
      camera.lookAt(0, -0.1, -0.7);
    },
  );
  return null;
}

/**
 * Lazy optional 3D showroom: track spots wash a wall with scallops over a reflective floor.
 * Lights ignite in sequence on load, aim toward the pointer and cross-fade between three display
 * temperatures. Reduced motion shows the static fallback and no canvas; off-screen canvases stop
 * rendering.
 * The scene is illustrative only: no product, photometric or manufacturer claim is implied.
 */
export default function LightingScene() {
  const [temperature, setTemperature] = useState<LightTemperature>("warm");
  const { ref, reduced, frameloop } = useScenePlayback<HTMLDivElement>();
  if (reduced) return <LightingFallback />;
  return (
    <div className="lighting-scene" ref={ref}>
      <Canvas
        frameloop={frameloop}
        dpr={[1, 1.75]}
        camera={{ position: [0, 0.2, 5.1], fov: 38 }}
        onCreated={({ camera }) => camera.lookAt(0, -0.1, -0.7)}
        fallback={<LightingFallback />}
        role="img"
        aria-label="Illustrative track lights washing a showroom wall"
      >
        <color attach="background" args={["#1b2120"]} />
        <fog attach="fog" args={["#1b2120", 6, 11]} />
        <ambientLight intensity={0.3} />
        <FlutedWall />
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, FLOOR_Y, 0]}>
          <planeGeometry args={[14, 8]} />
          <meshStandardMaterial color="#202624" roughness={0.32} metalness={0.25} />
        </mesh>
        <TrackHeads temperature={temperature} />
        <CameraDrift />
      </Canvas>
      <div className="scene-caption">
        <span>
          Track collection <small>Illustrative 3D scene</small>
        </span>
        <fieldset className="temperature-controls">
          <legend className="sr-only">Illustrative light temperature</legend>
          {(["warm", "neutral", "cool"] as const).map((option) => (
            <label key={option} title={`${option} light`}>
              <input
                type="radio"
                name="temperature"
                value={option}
                checked={temperature === option}
                onChange={() => setTemperature(option)}
              />
              <span className={`temperature-swatch swatch-${option}`} />
              <span className="sr-only">{option}</span>
            </label>
          ))}
        </fieldset>
      </div>
    </div>
  );
}
