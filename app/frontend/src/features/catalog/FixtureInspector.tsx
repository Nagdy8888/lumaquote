import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import {
  AdditiveBlending,
  CanvasTexture,
  Color,
  Vector3,
  type Group,
  type Mesh,
  type MeshBasicMaterial,
  type MeshStandardMaterial,
  type Object3D,
  type PointLight,
  type SpotLight,
} from "three";
import { RotateCw, X } from "lucide-react";
import { Button } from "@/shared/ui/button";
import {
  glowTexture,
  kelvinColour,
  studioEnvironment,
  useScenePlayback,
} from "@/features/showcase/sceneKit";
import { FAMILIES, familyOf } from "./fixtureModels";

const FLOOR_Y = -1.4;
const TEMPERATURES = [2700, 3000, 4000, 5000] as const;

/** Product fields the inspector shows; all come from the catalog row already on screen. */
export type InspectedProduct = {
  sku: string;
  name: string;
  lumens: number;
  ip_rating: string;
  cct: number | string;
};

let fade: CanvasTexture | null = null;

/**
 * Cached vertical alpha ramp for the light cone: opaque at the lens, transparent at the floor.
 * Errors: throws if a 2D context is unavailable; the page's SceneBoundary then removes the
 * inspector and the catalog stays usable.
 */
function fadeTexture() {
  if (fade) return fade;
  const canvas = document.createElement("canvas");
  canvas.width = 4;
  canvas.height = 128;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("2D canvas unavailable for light cone");
  const gradient = context.createLinearGradient(0, 0, 0, 128);
  gradient.addColorStop(0, "#ffffff");
  gradient.addColorStop(1, "#000000");
  context.fillStyle = gradient;
  context.fillRect(0, 0, 4, 128);
  fade = new CanvasTexture(canvas);
  return fade;
}

/** Pick the offered temperature nearest the product's own CCT, so the inspector opens true to it. */
function nearestTemperature(cct: number) {
  return TEMPERATURES.reduce((best, value) =>
    Math.abs(value - cct) < Math.abs(best - cct) ? value : best,
  );
}

/** Part of the model with its rest position and the direction it travels in the exploded view. */
type Part = { mesh: Mesh; rest: Vector3; travel: Vector3 };

/**
 * The installed fixture with its light: lens glow, a spot or point light, an additive light cone
 * for downward lamps and a pool on the floor. Inputs: `family`, `colour` (#rrggbb), `on`,
 * `exploded`, `yaw` (radians, from the Turn button). Every change eases in useFrame; nothing sets
 * React state per frame. The exploded view moves each part outward from the model centre along its
 * own offset, further for the lens, like an assembly drawing.
 */
function InspectorModel({
  family,
  colour,
  on,
  exploded,
  yaw,
}: {
  family: string;
  colour: string;
  on: boolean;
  exploded: boolean;
  yaw: number;
}) {
  const spec = FAMILIES[familyOf(family)];
  const turn = useRef<Group>(null);
  const model = useRef<Group>(null);
  const lens = useRef<MeshStandardMaterial>(null);
  const spot = useRef<SpotLight>(null);
  const aim = useRef<Object3D>(null);
  const point = useRef<PointLight>(null);
  const cone = useRef<MeshBasicMaterial>(null);
  const pool = useRef<MeshBasicMaterial>(null);
  const parts = useRef<Part[]>([]);
  const level = useRef(0);
  const spread = useRef(0);
  const tint = useMemo(() => new Color(), []);
  const scene = useThree((state) => state.scene);
  const gl = useThree((state) => state.gl);
  useEffect(
    /** Share the studio reflections with the tiles' scenes. */
    function applyEnvironment() {
      scene.environment = studioEnvironment(gl);
      scene.environmentIntensity = 0.6;
    },
    [scene, gl],
  );
  useEffect(
    /** Record every mesh's rest position and its exploded-view travel once the model mounts. */
    function collectParts() {
      const found: Part[] = [];
      model.current?.traverse(
        /** Keep meshes only; groups move with their children. */
        function visit(object) {
          const mesh = object as Mesh;
          if (!mesh.isMesh) return;
          const rest = mesh.position.clone();
          const isLens = mesh.material === lens.current;
          const direction =
            rest.lengthSq() < 0.0025 ? new Vector3() : rest.clone().normalize();
          const distance = 0.22 + rest.length() * 0.35 + (isLens ? 0.35 : 0);
          found.push({
            mesh,
            rest,
            travel: direction.multiplyScalar(distance),
          });
        },
      );
      parts.current = found;
    },
    [family],
  );
  useEffect(
    /** Point the spot at the floor below the lens; three needs the target object in the scene. */
    function aimSpot() {
      if (spot.current && aim.current) spot.current.target = aim.current;
    },
    [family],
  );
  useFrame(
    /** Ease light level, colour, explode distance and the turn toward their targets. */
    function animate(_state, delta) {
      const ease = 1 - Math.exp(-delta * 5);
      level.current += ((on ? 1 : 0) - level.current) * ease;
      spread.current += ((exploded ? 1 : 0) - spread.current) * ease;
      tint.set(colour);
      const glow = level.current;
      if (lens.current) {
        lens.current.emissive.lerp(tint, ease);
        lens.current.emissiveIntensity = 0.05 + glow * 2.6;
      }
      if (spot.current) {
        spot.current.color.lerp(tint, ease);
        spot.current.intensity = glow * 38;
      }
      if (point.current) {
        point.current.color.lerp(tint, ease);
        point.current.intensity = glow * 6;
      }
      if (cone.current) {
        cone.current.color.lerp(tint, ease);
        cone.current.opacity = glow * 0.16 * (1 - spread.current * 0.7);
      }
      if (pool.current) {
        pool.current.color.lerp(tint, ease);
        pool.current.opacity = glow * 0.55;
      }
      for (const part of parts.current) {
        part.mesh.position
          .copy(part.rest)
          .addScaledVector(part.travel, spread.current);
      }
      if (turn.current)
        turn.current.rotation.y += (yaw - turn.current.rotation.y) * ease;
    },
  );
  const beam = spec.beam;
  const coneHeight = beam ? beam.y - FLOOR_Y : 0;
  return (
    <>
      <group ref={turn}>
        <group ref={model}>
          <spec.Model lens={lens} />
        </group>
        {!beam && (
          <pointLight
            ref={point}
            position={spec.glow}
            distance={6}
            decay={1.5}
          />
        )}
      </group>
      {beam && (
        <>
          <spotLight
            ref={spot}
            position={[0, beam.y, 0]}
            angle={0.62}
            penumbra={0.5}
            distance={8}
            decay={1.3}
          />
          <object3D ref={aim} position={[0, FLOOR_Y, 0]} />
          <mesh position={[0, (beam.y + FLOOR_Y) / 2, 0]}>
            <cylinderGeometry
              args={[beam.radius, beam.radius * 3.2, coneHeight, 48, 1, true]}
            />
            <meshBasicMaterial
              ref={cone}
              alphaMap={fadeTexture()}
              transparent
              opacity={0}
              blending={AdditiveBlending}
              depthWrite={false}
            />
          </mesh>
        </>
      )}
      <mesh
        position={[0, FLOOR_Y + 0.005, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
        scale={[4.2, 4.2, 1]}
      >
        <planeGeometry />
        <meshBasicMaterial
          ref={pool}
          map={glowTexture()}
          transparent
          opacity={0}
          blending={AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
      <mesh position={[0, FLOOR_Y, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[16, 64]} />
        <meshStandardMaterial
          color="#252c2a"
          roughness={0.55}
          metalness={0.2}
        />
      </mesh>
    </>
  );
}

/**
 * Modal 3D inspector for one catalog product, opened from its tile. Inputs: `product` (fields
 * already shown on the card) and `onClose`. Controls are ordinary buttons and radios: light on/off,
 * colour temperature (opens at the temperature nearest the product's CCT), exploded view, and a
 * 45-degree turn for keyboard users; the canvas also orbits by drag and zooms by wheel. Side
 * effects: opens a native modal dialog (focus is trapped and Escape closes it) and one WebGL
 * context, both released on close. The model is illustrative, which the dialog says.
 */
export default function FixtureInspector({
  product,
  onClose,
}: {
  product: InspectedProduct;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const { ref, frameloop } = useScenePlayback<HTMLDivElement>();
  const [temperature, setTemperature] = useState(() =>
    nearestTemperature(Number(product.cct) || 3000),
  );
  const [on, setOn] = useState(true);
  const [exploded, setExploded] = useState(false);
  const [yaw, setYaw] = useState(0);
  const [touched, setTouched] = useState(false);
  const family = product.sku.slice(0, 2).toLowerCase();
  const titleId = `inspector-${product.sku}`;
  useEffect(
    /**
     * Open as a modal on mount. No cleanup closes it: an unmounted dialog leaves the top layer by
     * itself, and closing it here would fire `close` and unmount the inspector under StrictMode.
     */
    function openModal() {
      const element = dialog.current;
      if (element && !element.open) element.showModal();
    },
    [],
  );
  return (
    <dialog
      ref={dialog}
      className="fixture-inspector"
      aria-labelledby={titleId}
      onClose={onClose}
    >
      <header>
        <div>
          <h2 id={titleId}>
            {product.sku} · {product.name}
          </h2>
          <p>Illustrative 3D model, not a manufacturer drawing.</p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Close inspector"
          onClick={() => dialog.current?.close()}
        >
          <X />
        </Button>
      </header>
      <div className="inspector-body">
        <div
          ref={ref}
          className="inspector-stage"
          role="img"
          aria-label={`Illustrative 3D model of ${product.name}, ${on ? "lit" : "switched off"} at ${temperature} K${exploded ? ", shown as an exploded view" : ""}`}
          onPointerDown={() => setTouched(true)}
        >
          <Canvas
            frameloop={frameloop}
            dpr={[1, 2]}
            camera={{ position: [2.6, 0.9, 3.6], fov: 35 }}
            fallback={
              <p className="inspector-fallback">
                3D needs WebGL, which this browser has turned off.
              </p>
            }
          >
            <color attach="background" args={["#1d2321"]} />
            <fog attach="fog" args={["#1d2321", 7, 15]} />
            <ambientLight intensity={0.25} />
            <directionalLight position={[3, 4, 2]} intensity={1.1} />
            <directionalLight
              position={[-3, 1.5, -2]}
              intensity={0.45}
              color="#a9c1d4"
            />
            <InspectorModel
              family={family}
              colour={kelvinColour(temperature)}
              on={on}
              exploded={exploded}
              yaw={yaw}
            />
            <OrbitControls
              makeDefault
              enablePan={false}
              enableDamping
              autoRotate={!touched}
              autoRotateSpeed={0.7}
              minDistance={2.2}
              maxDistance={7}
              maxPolarAngle={1.5}
              target={[0, -0.35, 0]}
            />
          </Canvas>
        </div>
        <div className="inspector-controls">
          <p className="inspector-facts">
            {product.lumens.toLocaleString()} lm · {product.ip_rating} ·{" "}
            {product.cct}K
          </p>
          <fieldset>
            <legend>Colour temperature</legend>
            <div className="inspector-temperatures">
              {TEMPERATURES.map((value) => (
                <label key={value}>
                  <input
                    type="radio"
                    name={`${titleId}-cct`}
                    checked={temperature === value}
                    onChange={() => setTemperature(value)}
                  />
                  <span>
                    <i style={{ background: kelvinColour(value) }} />
                    {value} K
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
          <div className="inspector-toggles">
            <Button
              type="button"
              variant={on ? "default" : "outline"}
              aria-pressed={on}
              onClick={() => setOn((value) => !value)}
            >
              {on ? "Light on" : "Light off"}
            </Button>
            <Button
              type="button"
              variant={exploded ? "default" : "outline"}
              aria-pressed={exploded}
              onClick={() => setExploded((value) => !value)}
            >
              Exploded view
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setTouched(true);
                setYaw((value) => value + Math.PI / 4);
              }}
            >
              <RotateCw data-icon="inline-start" />
              Turn 45°
            </Button>
          </div>
          <small>Drag to turn the model. Scroll or pinch to zoom.</small>
        </div>
      </div>
    </dialog>
  );
}
