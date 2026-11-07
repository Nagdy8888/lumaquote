import { useMemo, useRef, type RefObject } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  AdditiveBlending,
  CanvasTexture,
  SRGBColorSpace,
  QuadraticBezierCurve3,
  Vector3,
  type Group,
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

/** One service shown around the hub; `level` is 1 connected, 0.5 configured but unverified, 0 off. */
export type HubNode = { key: string; name: string; level: number };

const labels = new Map<string, CanvasTexture>();

/**
 * Draw a service name into a cached 512x96 texture for a sprite label (no DOM roots, no font
 * download: it uses the page's own font). Side effect: one canvas per distinct name and level.
 * Errors: throws if a 2D context is unavailable; the SceneBoundary then removes the scene.
 */
function labelTexture(name: string, level: number) {
  const key = `${name}:${level}`;
  const cached = labels.get(key);
  if (cached) return cached;
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 96;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("2D canvas unavailable for hub label");
  const family = getComputedStyle(document.body).fontFamily || "sans-serif";
  context.font = `500 40px ${family}`;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillStyle = level > 0 ? "#d6ded0" : "#7f8b7b";
  context.fillText(name, 256, 48);
  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  labels.set(key, texture);
  return texture;
}

/** Brass ring and glowing core in the middle: the LumaQuote workspace. */
function Hub() {
  const ring = useRef<Group>(null);
  const core = useRef<MeshStandardMaterial>(null);
  const halo = useRef<SpriteMaterial>(null);
  useFrame(
    /** Ignite first, then keep the ring turning slowly. */
    function animate(state, delta) {
      const on = ignition(state.clock.elapsedTime, 0, 0.3, 0);
      if (ring.current) {
        ring.current.rotation.y += delta * 0.35;
        ring.current.rotation.x =
          0.5 + Math.sin(state.clock.elapsedTime * 0.4) * 0.12;
      }
      if (core.current) core.current.emissiveIntensity = 0.2 + on * 2.2;
      if (halo.current) halo.current.opacity = on * 0.75;
    },
  );
  return (
    <group>
      <group ref={ring}>
        <mesh>
          <torusGeometry args={[0.62, 0.035, 20, 96]} />
          <meshStandardMaterial
            color="#c9a46a"
            metalness={0.9}
            roughness={0.25}
          />
        </mesh>
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.5, 0.02, 16, 80]} />
          <meshStandardMaterial
            color="#c9a46a"
            metalness={0.9}
            roughness={0.3}
          />
        </mesh>
      </group>
      <mesh>
        <sphereGeometry args={[0.26, 40, 24]} />
        <meshStandardMaterial
          ref={core}
          color="#fff3df"
          emissive={LIGHT_COLOURS.warm}
          emissiveIntensity={0}
        />
      </mesh>
      <sprite scale={[2.6, 2.6, 1]}>
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
      <pointLight
        color={LIGHT_COLOURS.warm}
        intensity={6}
        distance={6}
        decay={1.5}
      />
    </group>
  );
}

/**
 * One satellite service with its cable and travelling light pulses toward the hub.
 * Inputs: `node` (name and light level), `index` (ignition order), `position` in scene units,
 * `labelHeight` (world units that keep the name about 12 CSS px tall).
 * Off services stay dark with no pulses; half-lit services pulse slower and dimmer.
 */
function Satellite({
  node,
  index,
  position,
  labelHeight,
}: {
  node: HubNode;
  index: number;
  position: Vector3;
  labelHeight: number;
}) {
  const curve = useMemo(
    () =>
      new QuadraticBezierCurve3(
        position,
        new Vector3(position.x * 0.5, position.y * 0.4 + 0.55, 0.3),
        new Vector3(0, 0, 0),
      ),
    [position],
  );
  const bead = useRef<MeshStandardMaterial>(null);
  const halo = useRef<SpriteMaterial>(null);
  const cable = useRef<MeshBasicMaterial>(null);
  const pulses = useRef<(Sprite | null)[]>([]);
  const point = useMemo(() => new Vector3(), []);
  useFrame(
    /** Light the node in turn, then run pulses along the cable while the service is connected. */
    function animate(state) {
      const time = state.clock.elapsedTime;
      const on = ignition(time, index + 1, 0.5, 0.22) * node.level;
      if (bead.current) bead.current.emissiveIntensity = 0.05 + on * 1.8;
      if (halo.current) halo.current.opacity = on * 0.6;
      if (cable.current) cable.current.opacity = 0.18 + on * 0.25;
      pulses.current.forEach(
        /** Advance one pulse along the cable; it fades in and out at the ends. */
        function move(pulse, k) {
          if (!pulse) return;
          const speed = node.level >= 1 ? 0.32 : 0.16;
          const t = (time * speed + k / 2 + index * 0.13) % 1;
          curve.getPoint(t, point);
          pulse.position.copy(point);
          (pulse.material as SpriteMaterial).opacity =
            on * Math.sin(t * Math.PI) * 0.9;
        },
      );
    },
  );
  return (
    <group>
      <mesh>
        <tubeGeometry args={[curve, 48, 0.012, 6, false]} />
        <meshBasicMaterial
          ref={cable}
          color="#a9967a"
          transparent
          opacity={0.18}
        />
      </mesh>
      <mesh position={position}>
        <sphereGeometry args={[0.15, 32, 20]} />
        <meshStandardMaterial
          ref={bead}
          color="#47534c"
          metalness={0.5}
          roughness={0.35}
          emissive={LIGHT_COLOURS.neutral}
          emissiveIntensity={0}
        />
      </mesh>
      <mesh position={position} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.21, 0.012, 10, 48]} />
        <meshStandardMaterial color="#c9a46a" metalness={0.9} roughness={0.3} />
      </mesh>
      <sprite position={position} scale={[1.1, 1.1, 1]}>
        <spriteMaterial
          ref={halo}
          map={glowTexture()}
          color={LIGHT_COLOURS.neutral}
          transparent
          opacity={0}
          blending={AdditiveBlending}
          depthWrite={false}
        />
      </sprite>
      {node.level > 0 &&
        [0, 1].map((k) => (
          <sprite
            key={k}
            ref={(sprite) => {
              pulses.current[k] = sprite;
            }}
            scale={[0.32, 0.32, 1]}
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
      <sprite
        position={[position.x, position.y - 0.36, position.z]}
        scale={[labelHeight * 5.33, labelHeight, 1]}
      >
        <spriteMaterial
          map={labelTexture(node.name, node.level)}
          transparent
          depthWrite={false}
        />
      </sprite>
    </group>
  );
}

/**
 * Place satellites on a flat ellipse around the hub, half on each side, sized to the canvas so the
 * labels never overlap; then add a slow camera drift that follows the pointer.
 */
function Constellation({ nodes }: { nodes: HubNode[] }) {
  const viewport = useThree((state) => state.viewport);
  const size = useThree((state) => state.size);
  const pixelsPerUnit = size.height / viewport.height;
  const labelHeight = 26 / pixelsPerUnit;
  const spreadX = Math.min(viewport.width * 0.36, 4.4);
  const spreadY = Math.min(viewport.height * 0.27, 1.15);
  const positions = useMemo(
    /** Split nodes left and right of the hub, evenly spaced on each side. */
    function layout() {
      const perSide = Math.ceil(nodes.length / 2);
      return nodes.map(
        /** Position one node on the ellipse; depth varies slightly for parallax. */
        function place(_node, index) {
          const left = index < perSide;
          const slot = left ? index : index - perSide;
          const count = left ? perSide : nodes.length - perSide;
          const share = count === 1 ? 0.5 : slot / (count - 1);
          const angle = (share - 0.5) * 1.35;
          const x = Math.cos(angle) * spreadX * (left ? -1 : 1);
          return new Vector3(
            x,
            -Math.sin(angle) * spreadY * 1.6,
            Math.sin(angle * 2) * 0.25,
          );
        },
      );
    },
    [nodes, spreadX, spreadY],
  );
  useFrame(
    /** Drift the camera a little and follow the pointer; conveys nothing, so it is safe to miss. */
    function drift(state) {
      const time = state.clock.elapsedTime;
      const camera = state.camera;
      camera.position.x +=
        (Math.sin(time * 0.15) * 0.3 +
          state.pointer.x * 0.45 -
          camera.position.x) *
        0.04;
      camera.position.y +=
        (0.45 + state.pointer.y * 0.25 - camera.position.y) * 0.04;
      camera.lookAt(0, 0, 0);
    },
  );
  return (
    <>
      <Hub />
      {nodes.map((node, index) => (
        <Satellite
          key={node.key}
          node={node}
          index={index}
          position={positions[index]}
          labelHeight={labelHeight}
        />
      ))}
    </>
  );
}

/** Floor disc that catches the hub's light. */
function Floor() {
  return (
    <mesh
      position={[0, -1.6, 0]}
      rotation={[-Math.PI / 2, 0, 0]}
      scale={[9, 4, 1]}
    >
      <planeGeometry />
      <meshBasicMaterial
        map={glowTexture()}
        color="#6b5a40"
        transparent
        opacity={0.55}
        blending={AdditiveBlending}
        depthWrite={false}
      />
    </mesh>
  );
}

/**
 * Decorative 3D map of the workspace and its services, lit from the same statuses the list below
 * shows. Inputs: `nodes`. Output: a 260px band, or null under reduced motion (no canvas). Hidden
 * from assistive technology: the list remains the accessible source of each status. Rendering
 * pauses off screen and in hidden tabs; no network assets are loaded.
 */
export default function ConnectionHub({ nodes }: { nodes: HubNode[] }) {
  const { ref, reduced, frameloop } = useScenePlayback<HTMLDivElement>();
  if (reduced) return null;
  return (
    <div ref={ref} className="connection-hub" aria-hidden="true">
      <Canvas
        frameloop={frameloop}
        dpr={[1, 1.75]}
        camera={{ position: [0, 0.45, 6.4], fov: 36 }}
        eventSource={ref as RefObject<HTMLElement>}
        eventPrefix="client"
        fallback={null}
      >
        <color attach="background" args={["#202727"]} />
        <fog attach="fog" args={["#202727", 6, 11]} />
        <ambientLight intensity={0.35} />
        <directionalLight position={[3, 4, 5]} intensity={1.1} />
        <Floor />
        <Constellation nodes={nodes} />
      </Canvas>
    </div>
  );
}
