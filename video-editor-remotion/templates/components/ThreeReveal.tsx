import React, { Suspense } from "react";
import {
  AbsoluteFill,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useGLTF, OrbitControls, Environment } from "@react-three/drei";

// ThreeReveal — 3D model rotating into view. Useful for Vhoe aircraft reveals,
// TriboTax 3D infographics (pyramid of taxation), product showcases.
//
// Plan usage:
//   { "kind": "three_reveal", "glb": "models/su-35.glb",
//     "rotation_speed": 0.6, "auto_rotate": true, "camera_z": 5,
//     "background_color": "#0A1A0F", "env_preset": "sunset" }
//
// Place .glb files in <remotion>/public/models/ before render.
// Requires npm packages: @remotion/three @react-three/fiber @react-three/drei three

type ModelProps = {
  glb: string;
  rotation: number;
  scale?: number;
};

const Model: React.FC<ModelProps> = ({ glb, rotation, scale = 1 }) => {
  const { scene } = useGLTF(staticFile(glb)) as any;
  return <primitive object={scene} rotation={[0, rotation, 0]} scale={scale} />;
};

export type ThreeRevealProps = {
  startFrame: number;
  endFrame: number;
  glb: string;
  rotation_speed?: number;
  auto_rotate?: boolean;
  camera_z?: number;
  scale?: number;
  background_color?: string;
  env_preset?: "sunset" | "dawn" | "night" | "warehouse" | "forest" | "city" | "park" | "studio";
};

export const ThreeReveal: React.FC<ThreeRevealProps> = ({
  startFrame, endFrame, glb,
  rotation_speed = 0.6, auto_rotate = true, camera_z = 5, scale = 1,
  background_color = "#0A1A0F", env_preset = "sunset",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const dur = endFrame - startFrame;
  const local = frame - startFrame;
  const fadeIn = interpolate(local, [0, fps * 0.5], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = local > dur - fps * 0.5
    ? interpolate(local, [dur - fps * 0.5, dur], [1, 0])
    : 1;
  const op = Math.min(fadeIn, fadeOut);

  const entry = spring({ frame: local, fps, config: { damping: 18 } });
  const rot = auto_rotate ? (local / fps) * rotation_speed : 0;

  return (
    <AbsoluteFill style={{
      pointerEvents: "none", opacity: op, background: background_color,
    }}>
      <ThreeCanvas width={width} height={height} camera={{ position: [0, 0, camera_z], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1.2} />
        <Suspense fallback={null}>
          <Model glb={glb} rotation={rot} scale={scale * entry} />
          <Environment preset={env_preset} />
        </Suspense>
        <OrbitControls enableZoom={false} enablePan={false} />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
