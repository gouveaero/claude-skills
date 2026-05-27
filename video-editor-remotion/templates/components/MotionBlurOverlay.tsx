import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { Trail, CameraMotionBlur } from "@remotion/motion-blur";

// MotionBlurOverlay — cinematic trail/motion-blur HOCs.
// Trail = stutter copies behind moving element (great for kinetic typography last word).
// CameraMotionBlur = applies blur on rapid camera moves (zooms, pans).
//
// Plan usage:
//   { "kind": "motion_blur", "mode": "trail", "child_text": "RÁPIDO",
//     "trail_layers": 8, "lag_in_frames": 2, "color": "#B87333" }
//
// Modes:
//   - "trail":  render a text/icon with N trailing copies fading behind
//   - "camera": wrap children in CameraMotionBlur for camera motion

export type MotionBlurOverlayProps = {
  startFrame: number;
  endFrame: number;
  mode?: "trail" | "camera";
  child_text?: string;
  font_size?: number;
  color?: string;
  trail_layers?: number;
  lag_in_frames?: number;
  shutter_angle?: number;
};

export const MotionBlurOverlay: React.FC<MotionBlurOverlayProps> = ({
  startFrame, endFrame,
  mode = "trail",
  child_text = "FAST",
  font_size = 200,
  color = "#B87333",
  trail_layers = 8,
  lag_in_frames = 2,
  shutter_angle = 180,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const local = frame - startFrame;
  const dur = endFrame - startFrame;
  const fadeIn = interpolate(local, [0, fps * 0.2], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = local > dur - fps * 0.3
    ? interpolate(local, [dur - fps * 0.3, dur], [1, 0])
    : 1;
  const op = Math.min(fadeIn, fadeOut);

  // Horizontal sweep across screen
  const sweep = spring({ frame: local, fps, config: { damping: 60, stiffness: 150 } });
  const x = interpolate(sweep, [0, 1], [-600, 0]);

  const textChild = (
    <div style={{
      fontSize: font_size, fontWeight: 900, color,
      fontFamily: "Inter, system-ui, sans-serif",
      letterSpacing: "-0.02em", textTransform: "uppercase",
      transform: `translateX(${x}px)`,
    }}>{child_text}</div>
  );

  if (mode === "camera") {
    return (
      <AbsoluteFill style={{
        pointerEvents: "none", opacity: op,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        <CameraMotionBlur shutterAngle={shutter_angle} samples={trail_layers}>
          {textChild}
        </CameraMotionBlur>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{
      pointerEvents: "none", opacity: op,
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <Trail layers={trail_layers} lagInFrames={lag_in_frames}>
        {textChild}
      </Trail>
    </AbsoluteFill>
  );
};
