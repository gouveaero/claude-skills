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

export type StackSegment = {
  label: string;
  value: number;
  color?: string;
};

export type StatStackedBarProps = {
  segments: StackSegment[];
  total: number; // numeric total to display ("60") — usually sum but allows custom
  prefix?: string;
  label?: string;
  start: number;
  end: number;
  position?: "center" | "top" | "bottom";
  brandColors?: BrandColors;
  fontFamily?: string;
};

export const StatStackedBar: React.FC<StatStackedBarProps> = ({
  segments,
  total,
  prefix = "+",
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
      <StackInner
        segments={segments}
        total={total}
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

const StackInner: React.FC<{
  segments: StackSegment[];
  total: number;
  prefix: string;
  label?: string;
  position: "center" | "top" | "bottom";
  brandColors: BrandColors;
  fontFamily: string;
  durationInFrames: number;
}> = ({ segments, total, prefix, label, position, brandColors, fontFamily, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const pop = spring({
    frame, fps, from: 0, to: 1,
    config: { damping: 12, stiffness: 200, mass: 0.55 },
  });

  const fadeOut = interpolate(
    frame,
    [Math.max(0, durationInFrames - 6), durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Each segment animates in sequentially — stagger 10 frames
  const STAGGER = 10;
  const SEG_DURATION = 14;
  const segmentTotal = segments.reduce((acc, s) => acc + s.value, 0);

  // Big counter value rises through segments
  let displayValue = 0;
  segments.forEach((seg, i) => {
    const segStart = 6 + i * STAGGER;
    const segEnd = segStart + SEG_DURATION;
    const localProgress = interpolate(frame, [segStart, segEnd], [0, 1], {
      extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });
    displayValue += seg.value * localProgress;
  });
  const counterValue = Math.round(displayValue);

  const TOTAL_WIDTH = 880;
  const BAR_HEIGHT = 80;

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
          transform: `scale(${0.55 + 0.45 * pop})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 26,
        }}
      >
        {/* Big counter */}
        <div
          style={{
            fontFamily, fontWeight: 900, fontSize: 240, lineHeight: 0.95,
            color: brandColors.keyword,
            WebkitTextStroke: `8px ${brandColors.stroke}`,
            paintOrder: "stroke fill",
            letterSpacing: "-0.04em",
            filter: `drop-shadow(0 0 24px ${brandColors.keyword}aa)`,
          }}
        >
          {prefix}{counterValue}
          <span style={{ fontSize: 140, color: "#FFFFFF" }}>%</span>
        </div>

        {/* Stacked horizontal bar */}
        <div
          style={{
            display: "flex",
            width: TOTAL_WIDTH,
            height: BAR_HEIGHT,
            borderRadius: 16,
            overflow: "hidden",
            border: "3px solid rgba(255,255,255,0.25)",
            boxShadow: "0 8px 30px rgba(0,0,0,0.5)",
            background: "rgba(255,255,255,0.08)",
          }}
        >
          {segments.map((seg, i) => {
            const segStart = 6 + i * STAGGER;
            const segEnd = segStart + SEG_DURATION;
            const segProgress = interpolate(frame, [segStart, segEnd], [0, 1], {
              extrapolateLeft: "clamp", extrapolateRight: "clamp",
            });
            const widthPx = (seg.value / segmentTotal) * TOTAL_WIDTH * segProgress;
            const color = seg.color ?? (i === 0 ? "#A04020" : i === 1 ? "#D17B2B" : brandColors.keyword);
            return (
              <div
                key={i}
                style={{
                  width: widthPx,
                  height: "100%",
                  background: color,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  borderRight: i < segments.length - 1 ? "2px solid rgba(0,0,0,0.3)" : "none",
                }}
              >
                {segProgress > 0.5 && widthPx > 80 ? (
                  <span
                    style={{
                      fontFamily, fontWeight: 900, fontSize: 36,
                      color: "#FFFFFF",
                      WebkitTextStroke: `3px ${brandColors.stroke}`,
                      paintOrder: "stroke fill",
                    }}
                  >
                    {seg.value}%
                  </span>
                ) : null}
              </div>
            );
          })}
        </div>

        {/* Segment labels below */}
        <div
          style={{
            display: "flex", width: TOTAL_WIDTH, justifyContent: "space-around",
            fontFamily, fontSize: 28, fontWeight: 700,
            color: "#FFFFFF",
            WebkitTextStroke: `4px ${brandColors.stroke}`,
            paintOrder: "stroke fill",
            textTransform: "uppercase",
            letterSpacing: "0.04em",
          }}
        >
          {segments.map((seg, i) => {
            const segStart = 6 + i * STAGGER;
            const segProgress = interpolate(frame, [segStart, segStart + SEG_DURATION], [0, 1], {
              extrapolateLeft: "clamp", extrapolateRight: "clamp",
            });
            return (
              <div key={i} style={{ opacity: segProgress, textAlign: "center" }}>
                {seg.label}
              </div>
            );
          })}
        </div>

        {label ? (
          <div
            style={{
              marginTop: 8,
              fontFamily, fontWeight: 800, fontSize: 44,
              color: brandColors.normal,
              WebkitTextStroke: `5px ${brandColors.stroke}`,
              paintOrder: "stroke fill",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            {label}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
