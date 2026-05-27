import React from "react";
import { useCurrentFrame, spring, useVideoConfig, interpolate } from "remotion";

interface LowerThirdProps {
  name: string;
  detail?: string;
  accentColor?: string;
  bgColor?: string;
  textColor?: string;
  positionY?: number; // 0-1, proporção da altura (default: 0.82)
}

export const LowerThird: React.FC<LowerThirdProps> = ({
  name,
  detail,
  accentColor = "#C8A96E",
  bgColor = "rgba(0,0,0,0.85)",
  textColor = "#FFFFFF",
  positionY = 0.82,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  const slideIn = spring({
    fps,
    frame,
    config: { damping: 20, stiffness: 180 },
  });
  const translateX = interpolate(slideIn, [0, 1], [-width * 0.5, 0]);
  const opacity = interpolate(slideIn, [0, 1], [0, 1]);

  // Fade out nos últimos 20 frames
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        top: positionY * height,
        transform: `translateX(${translateX}px)`,
        opacity: opacity * fadeOut,
        display: "flex",
        flexDirection: "row",
        overflow: "hidden",
      }}
    >
      {/* Accent bar */}
      <div style={{ width: 8, background: accentColor, flexShrink: 0 }} />
      {/* Content */}
      <div
        style={{
          background: bgColor,
          padding: "12px 24px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <span
          style={{
            fontFamily: "sans-serif",
            fontWeight: 800,
            fontSize: 40,
            color: textColor,
            lineHeight: 1.1,
            textTransform: "uppercase",
            letterSpacing: "1px",
          }}
        >
          {name}
        </span>
        {detail && (
          <span
            style={{
              fontFamily: "sans-serif",
              fontWeight: 400,
              fontSize: 28,
              color: accentColor,
              marginTop: 4,
            }}
          >
            {detail}
          </span>
        )}
      </div>
    </div>
  );
};
