import { useEffect, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { ContactShadows, OrbitControls } from "@react-three/drei";
import { LightingFallback } from "./SceneBoundary";

/** Build a procedural luminaire from geometry; no manufacturer or engineering-accuracy claim is implied. */
function Luminaire({ color }: { color: string }) {
  return (
    <group rotation={[0.12, 0, -0.1]}>
      <mesh position={[0, 0.8, 0]}>
        <boxGeometry args={[3.6, 0.08, 0.08]} />
        <meshStandardMaterial color="#343939" metalness={0.8} roughness={0.3} />
      </mesh>
      {[-1.2, 0, 1.2].map((x) => (
        <group key={x} position={[x, 0.61, 0]} rotation={[0.2, 0, 0.1]}>
          <mesh>
            <cylinderGeometry args={[0.06, 0.06, 0.4, 20]} />
            <meshStandardMaterial
              color="#333a39"
              metalness={0.8}
              roughness={0.3}
            />
          </mesh>
          <group position={[0, -0.44, 0]} rotation={[0.2, 0, -0.3]}>
            <mesh>
              <cylinderGeometry args={[0.21, 0.23, 0.52, 48]} />
              <meshStandardMaterial
                color="#b98a69"
                metalness={0.72}
                roughness={0.28}
              />
            </mesh>
            <mesh position={[0, -0.267, 0]}>
              <cylinderGeometry args={[0.184, 0.184, 0.015, 48]} />
              <meshStandardMaterial
                color={color}
                emissive={color}
                emissiveIntensity={2}
              />
            </mesh>
            <spotLight
              position={[0, -0.29, 0]}
              color={color}
              intensity={4}
              angle={0.5}
              penumbra={1}
            />
          </group>
        </group>
      ))}
    </group>
  );
}

/** Lazy optional 3D scene with user-controlled lighting and an immediate reduced-motion/WebGL fallback. */
export default function LightingScene() {
  const [temperature, setTemperature] = useState<"warm" | "neutral" | "cool">(
    "warm",
  );
  const [reduced, setReduced] = useState(
    () => matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  /** Follow changes in the user's motion preference and release the media-query listener on unmount. */
  useEffect(
    /** Observe system reduced-motion changes and return the matching listener cleanup. */
    function observeMotion() {
      const query = matchMedia("(prefers-reduced-motion: reduce)");
      /** Update the optional scene when system accessibility settings change. */
      function changed() {
        setReduced(query.matches);
      }
      query.addEventListener("change", changed);
      /** Detach the system preference listener when the scene is removed. */
      return function cleanup() {
        query.removeEventListener("change", changed);
      };
    },
    [],
  );
  if (reduced) return <LightingFallback />;
  const color = { warm: "#ffcf8a", neutral: "#fff0d8", cool: "#d8edff" }[
    temperature
  ];
  return (
    <div className="lighting-scene">
      <Canvas
        frameloop="demand"
        dpr={[1, 1.5]}
        camera={{ position: [3, 2.1, 4.8], fov: 40 }}
        fallback={<LightingFallback />}
        aria-label="Illustrative adjustable track-light scene"
      >
        <ambientLight intensity={1.8} />
        <directionalLight position={[3, 5, 2]} intensity={4} />
        <directionalLight
          position={[-3, 1, -2]}
          color="#d8b69a"
          intensity={2}
        />
        <Luminaire color={color} />
        <ContactShadows
          position={[0, -0.6, 0]}
          opacity={0.4}
          blur={2}
          scale={8}
        />
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          minPolarAngle={0.4}
          maxPolarAngle={1.6}
        />
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
