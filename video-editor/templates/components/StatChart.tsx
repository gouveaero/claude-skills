import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { DEFAULT_BRAND_COLORS, SAFE_ZONES_INSTAGRAM_REEL, type BrandColors } from "./helpers";

export type StatChartProps = {
  value: number;
  prefix?: string;
  label?: string;
  start: number;
  end: number;
  position?: "center" | "top" | "bottom" | "top-right" | "top-left";
  brandColors?: BrandColors;
  fontFamily?: string;
};

export const StatChart: React.FC<StatChartProps> = ({
  value,
  prefix = "",
  label,
  start,
  end,
  position = "top",
  brandColors = DEFAULT_BRAND_COLORS,
  fontFamily = "Inter, system-ui, sans-serif",
}) => {
  const { fps } = useVideoConfig();
  const startFrame = Math.round(start * fps);
  const durationInFrames = Math.max(1, Math.round((end - start) * fps));

  return (
    <Sequence from={startFrame} durationInFrames={durationInFrames}>
      <ChartInner
        value={value}
        prefix={prefix}
        label={label}
        position={position}
        brandColors={brandColors}
        fontFamily={fontFamily}
        durationInFrames={durationInFrames}
      />
    </Sequence>
  );
};

const ChartInner: React.FC<{
  value: number;
  prefix: string;
  label?: string;
  position: "center" | "top" | "bottom" | "top-right" | "top-left";
  brandColors: BrandColors;
  fontFamily: string;
  durationInFrames: number;
}> = ({ value, prefix, label, position, brandColors, fontFamily, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const pop = spring({
    frame, fps, from: 0, to: 1,
    config: { damping: 10, stiffness: 180, mass: 0.65 },
  });
  const fillProgress = interpolate(frame, [6, 28], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const displayValue = Math.round(interpolate(frame, [6, 28], [0, value], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  }));
  const fadeOut = interpolate(
    frame,
    [Math.max(0, durationInFrames - 6), durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const RADIUS = 180;
  const STROKE = 28;
  const SIZE = (RADIUS + STROKE) * 2;
  const CIRC = 2 * Math.PI * RADIUS;
  const dashOffset = CIRC * (1 - fillProgress);
  const scale = 0.5 + 0.5 * pop;

  // Container alignment per position
  const justify =
    position === "top" || position === "top-right" || position === "top-left" ? "flex-start"
    : position === "bottom" ? "flex-end"
    : "center";
  const align =
    position === "top-right" ? "flex-end"
    : position === "top-left" ? "flex-start"
    : "center";
  // Use Instagram safe zone (avoids overlap with avatar/handle in top-third)
  const padTop = position === "top" || position === "top-right" || position === "top-left"
    ? `${SAFE_ZONES_INSTAGRAM_REEL.top + 20}px`
    : "0";
  const padX = (position === "top-right" || position === "top-left") ? "5%" : "0";

  return (
    <AbsoluteFill
      style={{
        justifyContent: justify,
        alignItems: align,
        opacity: fadeOut,
        paddingTop: padTop,
        paddingLeft: padX,
        paddingRight: padX,
      }}
    >
      <div style={{ transform: `scale(${scale})`, textAlign: "center" }}>
        <div style={{ position: "relative", width: SIZE, height: SIZE }}>
          <svg width={SIZE} height={SIZE} style={{ transform: "rotate(-90deg)" }}>
            <circle
              cx={SIZE / 2} cy={SIZE / 2} r={RADIUS}
              fill="transparent"
              stroke="rgba(255,255,255,0.18)"
              strokeWidth={STROKE}
            />
            <circle
              cx={SIZE / 2} cy={SIZE / 2} r={RADIUS}
              fill="transparent"
              stroke={brandColors.keyword}
              strokeWidth={STROKE}
              strokeDasharray={CIRC}
              strokeDashoffset={dashOffset}
              strokeLinecap="round"
              style={{ filter: `drop-shadow(0 0 14px ${brandColors.keyword}aa)` }}
            />
          </svg>
          <div
            style={{
              position: "absolute", inset: 0,
              display: "flex", alignItems: "center", justifyContent: "center",
              flexDirection: "column",
            }}
          >
            <div
              style={{
                fontFamily, fontWeight: 900, fontSize: 180, lineHeight: 1,
                color: "#FFFFFF",
                WebkitTextStroke: `7px ${brandColors.stroke}`,
                paintOrder: "stroke fill",
                letterSpacing: "-0.03em",
              }}
            >
              {prefix}{displayValue}
              <span style={{ fontSize: 110, marginLeft: -6 }}>%</span>
            </div>
          </div>
        </div>
        {label ? (
          <div
            style={{
              marginTop: 18,
              fontFamily, fontWeight: 800, fontSize: 44,
              color: brandColors.normal,
              WebkitTextStroke: `6px ${brandColors.stroke}`,
              paintOrder: "stroke fill",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
            }}
          >
            {label}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
