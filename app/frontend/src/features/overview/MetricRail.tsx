import { useMemo, useRef, type RefObject } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  AdditiveBlending,
  type MeshBasicMaterial,
  type MeshStandardMaterial,
  type Sprite,
  type SpriteMaterial,
} from "three";
import {
  glowTexture,
  ignition,
  LIGHT_COLOURS,
  useScenePlayback,
} from "@/features/showcase/sceneKit";

const MAX_BEADS = 12;
const RAIL_Y = 0.4;

/**
 * Brightness of one metric lamp. Pure. Zero stays a faint ember so an empty column still reads as
 * a lamp; ten or more is full brightness.
 */
function brightness(count: number) {
  return count <= 0 ? 0.08 : 0.35 + Math.min(count, 10) * 0.065;
}

/**
 * One lamp over one metric column: a small head on the rail, its halo, and up to 12 beads, one per
 * counted item. Inputs: `x` (scene units), `count` (the number printed below it), `index` (ignition
 * order), `pulses` (shared pulse sprites, read each frame so passing light brightens the lamp).
 */
function MetricLamp({
  x,
  count,
  index,
  pulses,
}: {
  x: number;
  count: number;
  index: number;
  pulses: RefObject<(Sprite | null)[]>;
}) {
  const lens = useRef<MeshStandardMaterial>(null);
  const halo = useRef<SpriteMaterial>(null);
  const cone = useRef<MeshBasicMaterial>(null);
  const beads = useRef<(MeshStandardMaterial | null)[]>([]);
  const shown = Math.min(count, MAX_BEADS);
  const level = brightness(count);
  useFrame(
    /** Ignite in turn, flare when a rail pulse passes, and light the beads one after another. */
    function animate(state) {
      const time = state.clock.elapsedTime;
      const on = ignition(time, index, 0.4, 0.18);
      let flare = 0;
      for (const pulse of pulses.current ?? []) {
        if (pulse)
          flare = Math.max(
            flare,
            Math.max(0, 1 - Math.abs(pulse.position.x - x) / 0.6),
          );
      }
      const glow = on * (level + flare * 0.35);
      if (lens.current) lens.current.emissiveIntensity = 0.1 + glow * 2.6;
      if (halo.current) halo.current.opacity = glow * 0.8;
      if (cone.current) cone.current.opacity = glow * 0.11;
      beads.current.forEach(
        /** Bead k lights shortly after the lamp, so the count visibly fills up. */
        function lightBead(bead, k) {
          if (!bead) return;
          const filled = ignition(time, index * 2 + k, 0.9, 0.06);
          bead.emissiveIntensity =
            filled * (1.2 + Math.sin(time * 2 + k) * 0.25);
        },
      );
    },
  );
  return (
    <group position={[x, 0, 0]}>
      <mesh position={[0, RAIL_Y - 0.09, 0]}>
        <cylinderGeometry args={[0.025, 0.025, 0.1, 10]} />
        <meshStandardMaterial color="#c9a46a" metalness={0.8} roughness={0.3} />
      </mesh>
      <mesh position={[0, RAIL_Y - 0.22, 0]} rotation={[0.35, 0, 0]}>
        <cylinderGeometry args={[0.07, 0.09, 0.2, 24]} />
        <meshStandardMaterial
          color="#39433d"
          metalness={0.6}
          roughness={0.35}
        />
      </mesh>
      <mesh
        position={[0, RAIL_Y - 0.32, 0.035]}
        rotation={[Math.PI / 2 + 0.35, 0, 0]}
      >
        <circleGeometry args={[0.075, 24]} />
        <meshStandardMaterial
          ref={lens}
          color="#fff4e2"
          emissive={LIGHT_COLOURS.warm}
          emissiveIntensity={0}
        />
      </mesh>
      <mesh position={[0, (RAIL_Y - 0.34 - 0.3) / 2, 0.02]}>
        <cylinderGeometry
          args={[0.07, 0.42, RAIL_Y - 0.34 + 0.3, 32, 1, true]}
        />
        <meshBasicMaterial
          ref={cone}
          color={LIGHT_COLOURS.warm}
          transparent
          opacity={0}
          blending={AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
      <sprite position={[0, RAIL_Y - 0.36, 0.1]} scale={[1.4, 1.4, 1]}>
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
      {Array.from({ length: shown }, (_, k) => (
        <mesh key={k} position={[(k - (shown - 1) / 2) * 0.11, -0.3, 0]}>
          <sphereGeometry args={[0.035, 16, 10]} />
          <meshStandardMaterial
            ref={(material) => {
              beads.current[k] = material;
            }}
            color="#fff2dc"
            emissive={LIGHT_COLOURS.warm}
            emissiveIntensity={0}
          />
        </mesh>
      ))}
    </group>
  );
}

/** The rail across all columns with light pulses travelling left to right. */
function Rail({ counts }: { counts: number[] }) {
  const viewport = useThree((state) => state.viewport);
  const pulses = useRef<(Sprite | null)[]>([]);
  const width = viewport.width;
  const xs = useMemo(
    () =>
      counts.map(
        (_count, index) => -width / 2 + (width * (index + 0.5)) / counts.length,
      ),
    [counts, width],
  );
  useFrame(
    /** Move each pulse along the rail; they wrap around so the flow never stops. */
    function flow(state) {
      const time = state.clock.elapsedTime;
      pulses.current.forEach(
        /** Place pulse k; the two pulses run half a lap apart. */
        function move(pulse, k) {
          if (!pulse) return;
          const t = (time * 0.09 + k / 2) % 1;
          pulse.position.x = -width / 2 - 0.5 + t * (width + 1);
          (pulse.material as SpriteMaterial).opacity =
            ignition(time, 0, 1.2, 0) * 0.9;
        },
      );
    },
  );
  return (
    <>
      <mesh position={[0, RAIL_Y, 0]}>
        <boxGeometry args={[width + 2, 0.045, 0.06]} />
        <meshStandardMaterial
          color="#39433d"
          metalness={0.6}
          roughness={0.35}
        />
      </mesh>
      {[0, 1].map((k) => (
        <sprite
          key={k}
          ref={(sprite) => {
            pulses.current[k] = sprite;
          }}
          position={[0, RAIL_Y, 0.05]}
          scale={[0.9, 0.35, 1]}
        >
          <spriteMaterial
            map={glowTexture()}
            color={LIGHT_COLOURS.warm}
            transparent
            opacity={0}
            blending={AdditiveBlending}
            depthWrite={false}
          />
        </sprite>
      ))}
      {counts.map((count, index) => (
        <MetricLamp
          key={index}
          x={xs[index]}
          count={count}
          index={index}
          pulses={pulses}
        />
      ))}
    </>
  );
}

/**
 * Decorative light rail above the Overview metric strip: one lamp per metric column, its brightness
 * and bead count following the stored count printed below it. Inputs: `counts` in column order.
 * Output: null under reduced motion (no canvas). Hidden from assistive technology; the strip's
 * text is the accessible source. Pauses off screen and in hidden tabs.
 */
export default function MetricRail({ counts }: { counts: number[] }) {
  const { ref, reduced, frameloop } = useScenePlayback<HTMLDivElement>();
  if (reduced) return null;
  return (
    <div ref={ref} className="metric-rail" aria-hidden="true">
      <Canvas
        frameloop={frameloop}
        dpr={[1, 1.75]}
        camera={{ position: [0, 0, 4], fov: 16 }}
        fallback={null}
      >
        <color attach="background" args={["#202727"]} />
        <ambientLight intensity={0.5} />
        <directionalLight position={[2, 3, 4]} intensity={1.1} />
        <Rail counts={counts} />
      </Canvas>
    </div>
  );
}
