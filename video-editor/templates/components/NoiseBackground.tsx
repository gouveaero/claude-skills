import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { noise2D, noise3D } from "@remotion/noise";

// NoiseBackground — animated procedural noise (perlin/simplex) for grungy, organic
// backgrounds. Useful as understated motion behind talking-head shots (replaces
// flat color BG with subtle life) or for film-grain overlays.
//
// Plan usage:
//   { "kind": "noise_background", "mode": "grain", "intensity": 0.18,
//     "scale": 4, "color_a": "#0A1A0F", "color_b": "#1F4D2C", "speed": 0.5 }
//
// Modes:
//   - "grain":   film-grain overlay (low opacity, dense)
//   - "flow":    flowing 2-color gradient driven by 3D noise
//   - "static":  static-tv noise pattern

export type NoiseBackgroundProps = {
  startFrame: number;
  endFrame: number;
  mode?: "grain" | "flow" | "static";
  intensity?: number;
  scale?: number;
  color_a?: string;
  color_b?: string;
  speed?: number;
  cell_size?: number;
};

export const NoiseBackground: React.FC<NoiseBackgroundProps> = ({
  startFrame, endFrame,
  mode = "flow",
  intensity = 0.4,
  scale = 4,
  color_a = "#0A1A0F",
  color_b = "#1F4D2C",
  speed = 0.5,
  cell_size = 40,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const local = frame - startFrame;
  const dur = endFrame - startFrame;
  const fadeIn = interpolate(local, [0, fps * 0.4], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = local > dur - fps * 0.5
    ? interpolate(local, [dur - fps * 0.5, dur], [1, 0])
    : 1;
  const op = Math.min(fadeIn, fadeOut);

  const t = (local / fps) * speed;
  const cols = Math.ceil(width / cell_size);
  const rows = Math.ceil(height / cell_size);

  // Pre-compute grid samples once per frame
  const cells: { x: number; y: number; v: number }[] = [];
  for (let i = 0; i < cols; i++) {
    for (let j = 0; j < rows; j++) {
      const nx = (i / cols) * scale;
      const ny = (j / rows) * scale;
      const v = mode === "flow"
        ? (noise3D("flow-seed", nx, ny, t) + 1) / 2
        : mode === "static"
        ? (noise2D(`static-${frame}`, nx, ny) + 1) / 2
        : (noise2D(`grain-${frame}`, nx * 8, ny * 8) + 1) / 2;
      cells.push({ x: i * cell_size, y: j * cell_size, v });
    }
  }

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op, background: color_a }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {cells.map((c, idx) => (
          <rect
            key={idx}
            x={c.x} y={c.y} width={cell_size} height={cell_size}
            fill={color_b}
            opacity={c.v * intensity}
          />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
