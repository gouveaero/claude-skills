import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

interface CountUpProps {
  target: number;
  prefix?: string;
  suffix?: string;
  durationFrames?: number;
  fontSize?: number;
  color?: string;
  accentColor?: string;
}

export const CountUp: React.FC<CountUpProps> = ({
  target,
  prefix = "",
  suffix = "",
  durationFrames = 60,
  fontSize = 120,
  color = "#FFFFFF",
  accentColor = "#C8A96E",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    fps,
    frame,
    config: { damping: 200, stiffness: 80, mass: 0.5 },
    durationInFrames: durationFrames,
  });

  const value = Math.round(interpolate(progress, [0, 1], [0, target]));

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "sans-serif",
        fontWeight: 900,
      }}
    >
      <span style={{ fontSize, color, letterSpacing: "-2px" }}>
        {prefix}
        <span style={{ color: accentColor }}>
          {value.toLocaleString("pt-BR")}
        </span>
        {suffix}
      </span>
    </div>
  );
};
