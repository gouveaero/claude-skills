import React from "react";
import { useCurrentFrame, spring, useVideoConfig, interpolate, Video } from "remotion";

interface PiPBrollProps {
  src: string;
  corner?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  sizePercent?: number; // % da largura da tela (default: 35)
  borderColor?: string;
  borderWidth?: number;
  startFrom?: number; // frame inicial do clip PiP
}

export const PiPBroll: React.FC<PiPBrollProps> = ({
  src,
  corner = "top-right",
  sizePercent = 35,
  borderColor = "#C8A96E",
  borderWidth = 3,
  startFrom = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const appear = spring({ fps, frame, config: { damping: 18, stiffness: 160 } });
  const scale = interpolate(appear, [0, 1], [0.5, 1]);
  const opacity = interpolate(appear, [0, 1], [0, 1]);

  const pipWidth = width * (sizePercent / 100);
  // Maintain source aspect ratio — use video's natural aspect if available,
  // otherwise fall back to the composition aspect ratio.
  const pipHeight = pipWidth * (height / width);
  const margin = 24;

  const positions: Record<string, React.CSSProperties> = {
    "top-left":     { top: margin, left: margin },
    "top-right":    { top: margin, right: margin },
    "bottom-left":  { bottom: margin, left: margin },
    "bottom-right": { bottom: margin, right: margin },
  };

  const origins: Record<string, string> = {
    "top-left":     "top left",
    "top-right":    "top right",
    "bottom-left":  "bottom left",
    "bottom-right": "bottom right",
  };

  return (
    <div
      style={{
        position: "absolute",
        ...positions[corner],
        width: pipWidth,
        height: pipHeight,
        transform: `scale(${scale})`,
        transformOrigin: origins[corner],
        opacity,
        border: `${borderWidth}px solid ${borderColor}`,
        borderRadius: 8,
        overflow: "hidden",
        boxShadow: "0 8px 32px rgba(0,0,0,0.6)",
      }}
    >
      <Video
        src={src}
        startFrom={startFrom}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
    </div>
  );
};
