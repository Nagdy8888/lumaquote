import { useMemo, useRef, type ReactNode, type RefObject } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { CanvasTexture, SRGBColorSpace, type Group, type Mesh } from "three";
import { glowTexture, useScenePlayback } from "@/features/showcase/sceneKit";

let paper: CanvasTexture | null = null;

/**
 * Draw one generic quotation sheet (header rule, line items, a total bar) into a cached texture.
 * It contains no customer, price or product text, so capture mode never needs to hide it.
 * Errors: throws if a 2D context is unavailable; the page's SceneBoundary then shows the icon.
 */
function paperTexture() {
  if (paper) return paper;
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 332;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("2D canvas unavailable for quotation sheet");
  context.fillStyle = "#fbfaf4";
  context.fillRect(0, 0, 256, 332);
  context.fillStyle = "#2f3833";
  context.fillRect(22, 24, 70, 12);
  context.fillStyle = "#c9a46a";
  context.fillRect(196, 22, 38, 16);
  context.fillStyle = "#d9dccf";
  for (let row = 0; row < 7; row += 1) {
    const y = 78 + row * 26;
    context.fillRect(22, y, 120 - (row % 3) * 18, 8);
    context.fillRect(196, y, 38, 8);
  }
  context.fillStyle = "#e9ebe1";
  context.fillRect(22, 266, 212, 34);
  context.fillStyle = "#7e5f44";
  context.fillRect(170, 278, 54, 10);
  paper = new CanvasTexture(canvas);
  paper.colorSpace = SRGBColorSpace;
  paper.anisotropy = 4;
  return paper;
}

/** Ease-out with a small overshoot, for sheets settling onto the stack. Pure; input 0..1. */
function settle(value: number) {
  const t = Math.min(1, Math.max(0, value));
  const c = 1.6;
  return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2;
}

/**
 * The stack: `count` sheets deal in one by one, then a brass approval seal presses onto the top
 * sheet. Afterwards the stack floats and leans toward the pointer. Motion mutates three.js objects
 * in useFrame only.
 */
function Stack({ count }: { count: number }) {
  const root = useRef<Group>(null);
  const sheets = useRef<(Group | null)[]>([]);
  const seal = useRef<Mesh>(null);
  const poses = useMemo(
    () =>
      Array.from({ length: count }, (_, index) => ({
        x: (index - (count - 1) / 2) * 0.16,
        y: index * 0.035,
        spin: (index - (count - 1) / 2) * 0.09,
      })),
    [count],
  );
  useFrame(
    /** Deal, stamp, then idle; the seal lands after the last sheet. */
    function animate(state) {
      const time = state.clock.elapsedTime;
      sheets.current.forEach(
        /** Drop one sheet into its fanned pose after its turn in the deal. */
        function place(sheet, index) {
          if (!sheet) return;
          const pose = poses[index];
          const p = settle((time - 0.25 - index * 0.22) / 0.65);
          sheet.position.set(pose.x, pose.y + (1 - p) * 1.6, 0);
          sheet.rotation.z = pose.spin + (1 - p) * 0.6;
          sheet.visible = time > 0.25 + index * 0.22;
        },
      );
      if (seal.current) {
        const start = 0.45 + count * 0.22 + 0.35;
        const p = settle((time - start) / 0.45);
        const top = poses[count - 1];
        seal.current.position.set(
          top.x + 0.22,
          top.y + 0.05 + (1 - p) * 0.9,
          0.36,
        );
        seal.current.scale.setScalar(Math.max(0.001, p));
      }
      if (root.current) {
        const float = Math.sin(time * 0.9) * 0.03;
        root.current.position.y = float;
        root.current.rotation.y +=
          (state.pointer.x * 0.35 - root.current.rotation.y) * 0.05;
        root.current.rotation.x +=
          (0.95 - state.pointer.y * 0.12 - root.current.rotation.x) * 0.05;
      }
    },
  );
  return (
    <group ref={root} rotation={[0.95, 0, 0]}>
      {poses.map((_pose, index) => (
        <group
          key={index}
          ref={(group) => {
            sheets.current[index] = group;
          }}
          visible={false}
        >
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[1, 1.3]} />
            <meshStandardMaterial map={paperTexture()} roughness={0.85} />
          </mesh>
        </group>
      ))}
      <mesh ref={seal} rotation={[0, 0.4, 0]} scale={0.001}>
        <cylinderGeometry args={[0.15, 0.15, 0.045, 48]} />
        <meshStandardMaterial
          color="#c9a46a"
          metalness={0.85}
          roughness={0.3}
        />
      </mesh>
      <mesh
        position={[0, -0.04, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
        scale={[2.2, 2.4, 1]}
      >
        <planeGeometry />
        <meshBasicMaterial
          map={glowTexture()}
          color="#3a3b30"
          transparent
          opacity={0.22}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}

/**
 * Decorative quotation stack shown beside the Quotations heading. Inputs: `sheets` (1-4, from the
 * number of revisions listed) and `fallback` (the static heading icon, shown when WebGL is
 * unavailable). Output: null under reduced motion. Hidden from assistive technology; the register
 * below carries every fact. Pauses off screen and in hidden tabs.
 */
export default function RevisionStack({
  sheets,
  fallback,
}: {
  sheets: number;
  fallback: ReactNode;
}) {
  const { ref, reduced, frameloop } = useScenePlayback<HTMLDivElement>();
  if (reduced) return <>{fallback}</>;
  return (
    <div ref={ref} className="revision-stack" aria-hidden="true">
      <Canvas
        frameloop={frameloop}
        dpr={[1, 2]}
        camera={{ position: [0, 0.35, 3.1], fov: 32 }}
        eventSource={ref as RefObject<HTMLElement>}
        eventPrefix="client"
        fallback={fallback}
      >
        <ambientLight intensity={0.9} />
        <directionalLight
          position={[1.5, 3, 2.5]}
          intensity={1.6}
          color="#fff1dc"
        />
        <directionalLight
          position={[-2, 1, 1]}
          intensity={0.4}
          color="#cfe0ef"
        />
        <Stack count={Math.min(4, Math.max(1, sheets))} />
      </Canvas>
    </div>
  );
}
