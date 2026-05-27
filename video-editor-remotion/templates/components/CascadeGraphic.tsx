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

export type CascadeGraphicProps = {
  values: string[]; // e.g. ["R$ 100K", "R$ 130K", "R$ 150K"]
  start: number;
  end: number;
  position?: "center" | "top" | "bottom";
  brandColors?: BrandColors;
  fontFamily?: string;
};

export const CascadeGraphic: React.FC<CascadeGraphicProps> = ({
  values,
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
      <CascadeInner
        values={values}
        position={position}
        brandColors={brandColors}
        fontFamily={fontFamily}
        durationInFrames={durationInFrames}
      />
    </Sequence>
  );
};

const CascadeInner: React.FC<{
  values: string[];
  position: "center" | "top" | "bottom";
  brandColors: BrandColors;
  fontFamily: string;
  durationInFrames: number;
}> = ({ values, position, brandColors, fontFamily, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Each value enters with a stagger of ~14 frames
  const STAGGER = 14;

  const fadeOut = interpolate(
    frame,
    [Math.max(0, durationInFrames - 6), durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Background dim panel pop-in
  const panelPop = spring({
    frame, fps, from: 0, to: 1,
    config: { damping: 14, stiffness: 200, mass: 0.5 },
  });

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
          transform: `scale(${0.85 + 0.15 * panelPop})`,
          background: "rgba(10, 26, 15, 0.78)",
          padding: "60px 70px",
          borderRadius: 32,
          border: `4px solid ${brandColors.keyword}`,
          boxShadow: `0 20px 80px rgba(0,0,0,0.6), 0 0 60px ${brandColors.keyword}33`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 28,
        }}
      >
        {values.map((v, i) => {
          const wordFrame = frame - i * STAGGER;
          const enter = spring({
            frame: wordFrame, fps, from: 0, to: 1,
            config: { damping: 11, stiffness: 220, mass: 0.6 },
          });
          const x = (1 - enter) * -120;
          const isLast = i === values.length - 1;
          const colorEscalate = interpolate(i, [0, values.length - 1], [0.85, 1]);

          return (
            <React.Fragment key={i}>
              {i > 0 && (
                <div
                  style={{
                    fontFamily,
                    fontSize: 80,
                    color: brandColors.keyword,
                    fontWeight: 900,
                    opacity: enter,
                    lineHeight: 0.6,
                    transform: `translateY(${(1 - enter) * 10}px)`,
                  }}
                >
                  ↓
                </div>
              )}
              <div
                style={{
                  fontFamily,
                  fontWeight: 900,
                  fontSize: isLast ? 180 : 150,
                  color: isLast ? brandColors.keyword : "#FFFFFF",
                  WebkitTextStroke: `${isLast ? 12 : 10}px ${brandColors.stroke}`,
                  paintOrder: "stroke fill",
                  letterSpacing: "-0.02em",
                  opacity: enter,
                  transform: `translateX(${x}px) scale(${0.7 + 0.3 * enter})`,
                  transformOrigin: "center center",
                  filter: isLast ? `drop-shadow(0 0 30px ${brandColors.keyword}aa)` : "none",
                }}
              >
                {v}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
