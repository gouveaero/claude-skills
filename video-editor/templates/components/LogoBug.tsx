import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";

export type LogoBugProps = {
  logoSrc?: string;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left";
  opacity?: number;
  size?: number;
};

export const LogoBug: React.FC<LogoBugProps> = ({
  logoSrc,
  position = "top-right",
  opacity = 0.7,
  size = 140,
}) => {
  const frame = useCurrentFrame();
  if (!logoSrc) return null;

  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const inset: React.CSSProperties = {};
  if (position.startsWith("top")) inset.top = 60;
  else inset.bottom = 60;
  if (position.endsWith("right")) inset.right = 60;
  else inset.left = 60;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <Img
        src={staticFile(logoSrc)}
        style={{
          position: "absolute",
          width: size,
          height: "auto",
          opacity: opacity * fadeIn,
          filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.5))",
          ...inset,
        }}
      />
    </AbsoluteFill>
  );
};
