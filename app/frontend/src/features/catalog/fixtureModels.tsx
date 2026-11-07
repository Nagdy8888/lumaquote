import type { ReactNode, RefObject } from "react";
import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { RoundedBox } from "@react-three/drei";
import {
  DoubleSide,
  LatheGeometry,
  Vector2,
  type MeshBasicMaterial,
  type MeshStandardMaterial,
} from "three";
import { LIGHT_COLOURS } from "@/features/showcase/sceneKit";

/*
 * Illustrative fixture models shared by the catalog tiles and the 3D inspector. Built from
 * primitives in code (no downloaded assets); proportions are not manufacturer drawings.
 */

export type Family = "dl" | "tr" | "hb" | "ln" | "em" | "od";

export type Lens = RefObject<MeshStandardMaterial | null>;

/**
 * Shape description for one family. `tilt` and `glow` pose it for a catalog tile; `beam` is the
 * downward lens (height of its centre and radius, untilted) for the inspector's light cone, or null
 * when the lamp does not point straight down.
 */
export type FamilySpec = {
  tilt: [number, number, number];
  beam: { y: number; radius: number } | null;
  glow: [number, number, number];
  halo: number;
  colour: string;
  Model: (props: { lens: Lens }) => ReactNode;
};

/** Painted metal of fixture bodies. */
function Housing() {
  return (
    <meshStandardMaterial color="#39433d" metalness={0.6} roughness={0.36} />
  );
}

/** Brushed brass trim; the shared studio environment supplies its highlights. */
function Brass() {
  return (
    <meshStandardMaterial color="#c9a46a" metalness={0.92} roughness={0.26} />
  );
}

/** Emissive diffuser whose intensity the stage animates through `lens`. */
function LensMaterial({ lens, colour }: { lens: Lens; colour: string }) {
  return (
    <meshStandardMaterial
      ref={lens}
      color="#fff6e8"
      emissive={colour}
      emissiveIntensity={0}
      roughness={0.4}
      side={DoubleSide}
    />
  );
}

/** Recessed downlight: a can with a brass trim ring and a round lens on its underside. */
function Downlight({ lens }: { lens: Lens }) {
  return (
    <group>
      <mesh position={[0, 0.27, 0]}>
        <cylinderGeometry args={[0.28, 0.3, 0.14, 40]} />
        <Housing />
      </mesh>
      <mesh>
        <cylinderGeometry args={[0.5, 0.46, 0.42, 56]} />
        <Housing />
      </mesh>
      <mesh position={[0, -0.21, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.5, 0.055, 18, 72]} />
        <Brass />
      </mesh>
      <mesh position={[0, -0.215, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.38, 56]} />
        <LensMaterial lens={lens} colour={LIGHT_COLOURS.warm} />
      </mesh>
    </group>
  );
}

/** Track spot: a rail, adapter, stem and an angled cylindrical head. */
function TrackSpot({ lens }: { lens: Lens }) {
  return (
    <group position={[0, 0.1, 0]}>
      <mesh position={[0, 0.62, 0]}>
        <boxGeometry args={[1.8, 0.09, 0.14]} />
        <Housing />
      </mesh>
      <mesh position={[0, 0.52, 0]}>
        <boxGeometry args={[0.24, 0.12, 0.18]} />
        <Housing />
      </mesh>
      <mesh position={[0, 0.33, 0]}>
        <cylinderGeometry args={[0.035, 0.035, 0.34, 16]} />
        <Brass />
      </mesh>
      <mesh position={[0, 0.15, 0]}>
        <sphereGeometry args={[0.075, 24, 16]} />
        <Brass />
      </mesh>
      <group position={[0, 0.12, 0]} rotation={[-1.05, 0, 0.3]}>
        <mesh position={[0, -0.3, 0]}>
          <cylinderGeometry args={[0.2, 0.25, 0.62, 48]} />
          <Housing />
        </mesh>
        <mesh position={[0, -0.61, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.245, 0.028, 14, 56]} />
          <Brass />
        </mesh>
        <mesh position={[0, -0.612, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <circleGeometry args={[0.21, 48]} />
          <LensMaterial lens={lens} colour={LIGHT_COLOURS.warm} />
        </mesh>
      </group>
    </group>
  );
}

const BELL = new LatheGeometry(
  [
    [0.13, 0.42],
    [0.16, 0.3],
    [0.32, 0.16],
    [0.52, -0.06],
    [0.62, -0.24],
    [0.65, -0.3],
  ].map(([x, y]) => new Vector2(x, y)),
  64,
);

/** High-bay bell with a driver can and a hanging hook. */
function HighBay({ lens }: { lens: Lens }) {
  return (
    <group position={[0, 0.05, 0]}>
      <mesh position={[0, 0.6, 0]}>
        <torusGeometry args={[0.07, 0.018, 10, 32]} />
        <Brass />
      </mesh>
      <mesh position={[0, 0.48, 0]}>
        <cylinderGeometry args={[0.17, 0.17, 0.2, 40]} />
        <Housing />
      </mesh>
      <mesh geometry={BELL}>
        <meshStandardMaterial
          color="#39433d"
          metalness={0.6}
          roughness={0.36}
          side={DoubleSide}
        />
      </mesh>
      <mesh position={[0, -0.3, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.65, 0.03, 12, 72]} />
        <Brass />
      </mesh>
      <mesh position={[0, -0.24, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.6, 64]} />
        <LensMaterial lens={lens} colour={LIGHT_COLOURS.neutral} />
      </mesh>
    </group>
  );
}

/** Suspended linear profile with a diffuser strip, brass end caps and two cables. */
function Linear({ lens }: { lens: Lens }) {
  return (
    <group>
      {[-0.72, 0.72].map((x) => (
        <mesh key={x} position={[x, 0.55, 0]}>
          <cylinderGeometry args={[0.007, 0.007, 1, 6]} />
          <meshStandardMaterial
            color="#8b8f86"
            metalness={0.8}
            roughness={0.3}
          />
        </mesh>
      ))}
      <mesh>
        <boxGeometry args={[1.9, 0.14, 0.22]} />
        <Housing />
      </mesh>
      {[-0.965, 0.965].map((x) => (
        <mesh key={x} position={[x, 0, 0]}>
          <boxGeometry args={[0.035, 0.16, 0.24]} />
          <Brass />
        </mesh>
      ))}
      <mesh position={[0, -0.075, 0]}>
        <boxGeometry args={[1.86, 0.02, 0.17]} />
        <LensMaterial lens={lens} colour={LIGHT_COLOURS.neutral} />
      </mesh>
    </group>
  );
}

/** Emergency luminaire: a white body, a front diffuser and a small charge indicator. */
function Emergency({ lens }: { lens: Lens }) {
  const led = useRef<MeshBasicMaterial>(null);
  useFrame(
    /** Pulse the charge indicator slowly; purely decorative. */
    function pulse(state) {
      if (led.current)
        led.current.opacity =
          0.55 + Math.sin(state.clock.elapsedTime * 2.4) * 0.45;
    },
  );
  return (
    <group>
      <RoundedBox args={[1.15, 0.38, 0.26]} radius={0.06} smoothness={4}>
        <meshStandardMaterial
          color="#e6ebdd"
          metalness={0.05}
          roughness={0.55}
        />
      </RoundedBox>
      <mesh position={[-0.05, 0.01, 0.132]}>
        <planeGeometry args={[0.9, 0.22]} />
        <LensMaterial lens={lens} colour={LIGHT_COLOURS.cool} />
      </mesh>
      <mesh position={[0.47, -0.1, 0.135]}>
        <circleGeometry args={[0.028, 20]} />
        <meshBasicMaterial
          ref={led}
          color="#62e08d"
          transparent
          toneMapped={false}
        />
      </mesh>
    </group>
  );
}

/** Outdoor wall lantern: backplate, arm, framed glass and a pyramid cap. */
function Outdoor({ lens }: { lens: Lens }) {
  return (
    <group position={[0, -0.05, 0.1]}>
      <mesh position={[0, 0.05, -0.42]}>
        <boxGeometry args={[0.36, 0.95, 0.06]} />
        <Housing />
      </mesh>
      <mesh position={[0, 0.28, -0.3]}>
        <boxGeometry args={[0.07, 0.07, 0.22]} />
        <Housing />
      </mesh>
      <mesh position={[0, 0.03, 0]}>
        <boxGeometry args={[0.38, 0.5, 0.38]} />
        <LensMaterial lens={lens} colour={LIGHT_COLOURS.warm} />
      </mesh>
      {[
        [-1, -1],
        [-1, 1],
        [1, -1],
        [1, 1],
      ].map(([x, z]) => (
        <mesh key={`${x}${z}`} position={[x * 0.2, 0.03, z * 0.2]}>
          <boxGeometry args={[0.045, 0.52, 0.045]} />
          <Housing />
        </mesh>
      ))}
      <mesh position={[0, 0.39, 0]} rotation={[0, Math.PI / 4, 0]}>
        <coneGeometry args={[0.36, 0.24, 4]} />
        <Housing />
      </mesh>
      <mesh position={[0, -0.25, 0]}>
        <boxGeometry args={[0.46, 0.06, 0.46]} />
        <Brass />
      </mesh>
    </group>
  );
}

export const FAMILIES: Record<Family, FamilySpec> = {
  dl: {
    beam: { y: -0.22, radius: 0.36 },
    tilt: [-0.95, 0, 0],
    glow: [0, -0.15, 0.22],
    halo: 1.5,
    colour: LIGHT_COLOURS.warm,
    Model: Downlight,
  },
  tr: {
    beam: null,
    tilt: [0.05, 0, 0],
    glow: [0.15, -0.2, 0.55],
    halo: 1.1,
    colour: LIGHT_COLOURS.warm,
    Model: TrackSpot,
  },
  hb: {
    beam: { y: -0.26, radius: 0.55 },
    tilt: [-0.7, 0, 0],
    glow: [0, -0.15, 0.3],
    halo: 1.9,
    colour: LIGHT_COLOURS.neutral,
    Model: HighBay,
  },
  ln: {
    beam: { y: -0.09, radius: 0.45 },
    tilt: [-0.5, 0, 0.04],
    glow: [0, -0.1, 0.1],
    halo: 2.2,
    colour: LIGHT_COLOURS.neutral,
    Model: Linear,
  },
  em: {
    beam: null,
    tilt: [0.15, 0, 0],
    glow: [-0.05, 0, 0.2],
    halo: 1.6,
    colour: LIGHT_COLOURS.cool,
    Model: Emergency,
  },
  od: {
    beam: null,
    tilt: [0.12, 0, 0],
    glow: [0, 0, 0.15],
    halo: 1.5,
    colour: LIGHT_COLOURS.warm,
    Model: Outdoor,
  },
};

/** Map a catalog SKU prefix to a modelled family; unknown prefixes show the downlight. */
export function familyOf(code: string): Family {
  return code in FAMILIES ? (code as Family) : "dl";
}
