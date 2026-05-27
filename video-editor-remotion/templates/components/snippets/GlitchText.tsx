import React from "react";
import { useCurrentFrame, spring, useVideoConfig, interpolate } from "remotion";

interface GlitchTextProps {
  text: string;
  fontSize?: number;
  color?: string;
  intensity?: number; // 1-10
  durationFrames?: number;
}

export const GlitchText: React.FC<GlitchTextProps> = ({
  text,
  fontSize = 80,
  color = "#FFFFFF",
  intensity = 5,
  durationFrames = 20,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const glitchActive = frame < durationFrames;
  const offset = glitchActive ? Math.sin(frame * 2.5) * intensity : 0;
  const offsetY = glitchActive ? Math.cos(frame * 1.8) * (intensity * 0.4) : 0;

  const entrySpring = spring({
    fps,
    frame,
    config: { damping: 12, stiffness: 220, mass: 0.8 },
    durationInFrames: durationFrames,
  });
  const entryOpacity = interpolate(entrySpring, [0, 1], [0, 1]);
  const entryScale = interpolate(entrySpring, [0, 1], [0.85, 1]);

  const baseStyle: React.CSSProperties = {
    fontFamily: "sans-serif",
    fontWeight: 900,
    fontSize,
    position: "absolute",
    whiteSpace: "nowrap",
    top: 0,
    left: 0,
  };

  return (
    <div
      style={{
        position: "relative",
        display: "inline-block",
        opacity: entryOpacity,
        transform: `scale(${entryScale})`,
      }}
    >
      {/* Red channel */}
      <span
        style={{
          ...baseStyle,
          color: "rgba(255,0,0,0.7)",
          transform: `translate(${offset}px, ${offsetY}px)`,
          mixBlendMode: "screen",
        }}
      >
        {text}
      </span>
      {/* Blue channel */}
      <span
        style={{
          ...baseStyle,
          color: "rgba(0,100,255,0.7)",
          transform: `translate(${-offset}px, ${-offsetY}px)`,
          mixBlendMode: "screen",
        }}
      >
        {text}
      </span>
      {/* Main — sits on top, drives layout height */}
      <span style={{ ...baseStyle, color, position: "relative" }}>{text}</span>
    </div>
  );
};
