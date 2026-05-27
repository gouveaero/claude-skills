import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { makeCircle, makeTriangle, makeRect, makeStar, makePolygon } from "@remotion/shapes";
import { evolvePath, interpolatePath, resetPath, getLength, getPointAtLength } from "@remotion/paths";

// ShapeMorph — geometric shape morph (circle → triangle → star) with stroke-draw entry.
// Built on @remotion/shapes (primitive generators) + @remotion/paths (path interpolation).
// Useful for abstract intros, brand icon reveals, and animated dividers.
//
// Plan usage:
//   { "kind": "shape_morph", "from_shape": "circle", "to_shape": "star",
//     "size": 320, "stroke_color": "#B87333", "fill_color": "#F5F1E8",
//     "stroke_width": 8, "position": "center", "stroke_draw_seconds": 1.0 }

type ShapeKind = "circle" | "triangle" | "rect" | "star" | "polygon";

const buildPath = (kind: ShapeKind, size: number): string => {
  const r = size / 2;
  if (kind === "circle") return makeCircle({ radius: r }).path;
  if (kind === "triangle") return makeTriangle({ length: size }).path;
  if (kind === "rect") return makeRect({ width: size, height: size }).path;
  if (kind === "star") return makeStar({ innerRadius: r * 0.5, outerRadius: r, points: 5 }).path;
  return makePolygon({ sides: 6, radius: r }).path;
};

export type ShapeMorphProps = {
  startFrame: number;
  endFrame: number;
  from_shape?: ShapeKind;
  to_shape?: ShapeKind;
  size?: number;
  stroke_color?: string;
  fill_color?: string;
  stroke_width?: number;
  position?: "center" | "top-right" | "top-left" | "bottom-right" | "bottom-left";
  stroke_draw_seconds?: number;
};

export const ShapeMorph: React.FC<ShapeMorphProps> = ({
  startFrame, endFrame,
  from_shape = "circle", to_shape = "star",
  size = 320,
  stroke_color = "#B87333",
  fill_color = "transparent",
  stroke_width = 8,
  position = "center",
  stroke_draw_seconds = 1.0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const local = frame - startFrame;
  const dur = endFrame - startFrame;

  const strokeFrames = Math.max(1, Math.round(stroke_draw_seconds * fps));
  const fromPath = buildPath(from_shape, size);
  const toPath = buildPath(to_shape, size);

  // Morph timing: stroke draws in first half, morph in second half
  const morphT = interpolate(local, [strokeFrames, dur - strokeFrames * 0.5], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const morphedPath = interpolatePath(morphT, fromPath, toPath);
  const safePath = resetPath(morphedPath);
  const len = getLength(safePath);

  // Stroke-draw on entry
  const draw = interpolate(local, [0, strokeFrames], [0, 1], { extrapolateRight: "clamp" });
  const dashOffset = (1 - draw) * len;

  // Subtle bobbing through the whole duration
  const wobble = Math.sin(local / 18) * 4;
  const entry = spring({ frame: local, fps, config: { damping: 14 } });
  const exit = local > dur - fps * 0.4
    ? interpolate(local, [dur - fps * 0.4, dur], [1, 0])
    : 1;

  // Demonstrate evolvePath for a small orbiting marker
  const orbit = evolvePath(morphT, safePath);
  // getPointAtLength gives us a coordinate on the path for the orbit marker
  const orbitPoint = getPointAtLength(safePath, len * (orbit.strokeDashoffset === 0 ? 0 : 1 - orbit.strokeDashoffset / len));

  const pos: React.CSSProperties =
    position === "center" ? { left: "50%", top: "50%", transform: `translate(-50%, ${wobble}px) scale(${entry})` } :
    position === "top-right" ? { top: 100, right: 80, transform: `translateY(${wobble}px) scale(${entry})` } :
    position === "top-left" ? { top: 100, left: 80, transform: `translateY(${wobble}px) scale(${entry})` } :
    position === "bottom-right" ? { bottom: 100, right: 80, transform: `translateY(${wobble}px) scale(${entry})` } :
    { bottom: 100, left: 80, transform: `translateY(${wobble}px) scale(${entry})` };

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: exit }}>
      <div style={{ position: "absolute", width: size, height: size, ...pos }}>
        <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} overflow="visible">
          <path
            d={safePath}
            fill={fill_color}
            stroke={stroke_color}
            strokeWidth={stroke_width}
            strokeLinejoin="round"
            strokeLinecap="round"
            strokeDasharray={len}
            strokeDashoffset={dashOffset}
          />
          <circle cx={orbitPoint.x} cy={orbitPoint.y} r={stroke_width * 1.5} fill={stroke_color} />
        </svg>
      </div>
    </AbsoluteFill>
  );
};
