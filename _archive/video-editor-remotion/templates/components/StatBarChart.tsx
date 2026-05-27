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

export type StatBarChartProps = {
  value: number;
  prefix?: string;
  label?: string;
  start: number;
  end: number;
  position?: "center" | "top" | "bottom";
  brandColors?: BrandColors;
  fontFamily?: string;
};

export const StatBarChart: React.FC<StatBarChartProps> = ({
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
      <BarInner
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

const BarInner: React.FC<{
  value: number;
  prefix: string;
  label?: string;
  position: "center" | "top" | "bottom";
  brandColors: BrandColors;
  fontFamily: string;
  durationInFrames: number;
}> = ({ value, prefix, label, position, brandColors, fontFamily, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const pop = spring({
    frame, fps, from: 0, to: 1,
    config: { damping: 11, stiffness: 200, mass: 0.6 },
  });
  const fillProgress = interpolate(frame, [6, 30], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const displayValue = Math.round(interpolate(frame, [6, 30], [0, value], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  }));
  const fadeOut = interpolate(
    frame,
    [Math.max(0, durationInFrames - 6), durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const BAR_HEIGHT = 480;
  const BAR_WIDTH = 200;
  const filledHeight = BAR_HEIGHT * fillProgress;

  const justify = position === "top" ? "flex-start" : position === "bottom" ? "flex-end" : "center";
  const padTop = position === "top" ? `${SAFE_ZONES_INSTAGRAM_REEL.top + 20}px` : "0";

  return (
    <AbsoluteFill
      style={{
        justifyContent: justify,
        alignItems: "center",
        opacity: fadeOut,
        paddingTop: padTop,
      }}
    >
      <div
        style={{
          transform: `scale(${0.6 + 0.4 * pop})`,
          display: "flex",
          flexDirection: "row",
          alignItems: "flex-end",
          gap: 36,
        }}
      >
        {/* Vertical bar */}
        <div
          style={{
            position: "relative",
            width: BAR_WIDTH,
            height: BAR_HEIGHT,
            background: "rgba(255,255,255,0.12)",
            borderRadius: 22,
            overflow: "hidden",
            border: `3px solid rgba(255,255,255,0.25)`,
            boxShadow: "0 12px 40px rgba(0,0,0,0.55)",
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              bottom: 0,
              height: filledHeight,
              background: `linear-gradient(180deg, ${brandColors.keyword} 0%, ${brandColors.keyword}cc 100%)`,
              borderRadius: "0 0 18px 18px",
              boxShadow: `0 0 30px ${brandColors.keyword}88`,
            }}
          />
          {/* Tick marks */}
          {[0.25, 0.5, 0.75].map((t) => (
            <div
              key={t}
              style={{
                position: "absolute",
                left: 0, right: 0,
                bottom: BAR_HEIGHT * t,
                height: 2,
                background: "rgba(255,255,255,0.2)",
              }}
            />
          ))}
        </div>
        {/* Number + label */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
          <div
            style={{
              fontFamily, fontWeight: 900, fontSize: 220, lineHeight: 0.95,
              color: brandColors.keyword,
              WebkitTextStroke: `8px ${brandColors.stroke}`,
              paintOrder: "stroke fill",
              letterSpacing: "-0.04em",
            }}
          >
            {prefix}{displayValue}
            <span style={{ fontSize: 130, color: "#FFFFFF" }}>%</span>
          </div>
          {label ? (
            <div
              style={{
                marginTop: 4,
                fontFamily, fontWeight: 800, fontSize: 42,
                color: brandColors.normal,
                WebkitTextStroke: `5px ${brandColors.stroke}`,
                paintOrder: "stroke fill",
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                maxWidth: 480,
              }}
            >
              {label}
            </div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};
