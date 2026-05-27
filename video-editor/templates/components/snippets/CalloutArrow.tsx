import React from "react";
import { useCurrentFrame, spring, useVideoConfig, interpolate } from "remotion";

interface CalloutArrowProps {
  label: string;
  targetX: number; // 0-1 (proporção da largura)
  targetY: number; // 0-1 (proporção da altura)
  direction?: "left" | "right" | "up" | "down";
  color?: string;
  fontSize?: number;
}

export const CalloutArrow: React.FC<CalloutArrowProps> = ({
  label,
  targetX,
  targetY,
  direction = "left",
  color = "#FFD700",
  fontSize = 36,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const appear = spring({ fps, frame, config: { damping: 15, stiffness: 200 } });
  const opacity = interpolate(appear, [0, 1], [0, 1]);
  const scale = interpolate(appear, [0, 1], [0.6, 1]);

  const x = targetX * width;
  const y = targetY * height;

  // SVG arrow sized relative to fontSize for consistent proportions
  const arrowSize = fontSize * 1.6;
  const rotations: Record<string, number> = {
    left: 180,
    right: 0,
    up: -90,
    down: 90,
  };
  const rotation = rotations[direction];

  const originMap: Record<string, string> = {
    right: "left center",
    left: "right center",
    up: "center bottom",
    down: "center top",
  };

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `scale(${scale})`,
        transformOrigin: originMap[direction],
        opacity,
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      {direction === "right" && (
        <svg
          width={arrowSize}
          height={arrowSize * 0.67}
          viewBox="0 0 60 40"
          style={{ transform: `rotate(${rotation}deg)`, flexShrink: 0 }}
        >
          <path
            d="M0 20 L40 20 M40 20 L25 5 M40 20 L25 35"
            stroke={color}
            strokeWidth="5"
            strokeLinecap="round"
            fill="none"
          />
        </svg>
      )}
      <span
        style={{
          fontFamily: "sans-serif",
          fontWeight: 700,
          fontSize,
          color,
          textShadow: "2px 2px 8px rgba(0,0,0,0.8)",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </span>
      {direction !== "right" && (
        <svg
          width={arrowSize}
          height={arrowSize * 0.67}
          viewBox="0 0 60 40"
          style={{ transform: `rotate(${rotation}deg)`, flexShrink: 0 }}
        >
          <path
            d="M0 20 L40 20 M40 20 L25 5 M40 20 L25 35"
            stroke={color}
            strokeWidth="5"
            strokeLinecap="round"
            fill="none"
          />
        </svg>
      )}
    </div>
  );
};
