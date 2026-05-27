import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { DEFAULT_BRAND_COLORS, type BrandColors } from "./helpers";

export type StatOverlayProps = {
  text: string;
  subtext?: string;
  start: number;
  end: number;
  brandColors?: BrandColors;
  fontFamily?: string;
};

export const StatOverlay: React.FC<StatOverlayProps> = ({
  text,
  subtext,
  start,
  end,
  brandColors = DEFAULT_BRAND_COLORS,
  fontFamily = "Inter, system-ui, sans-serif",
}) => {
  const { fps } = useVideoConfig();
  const startFrame = Math.round(start * fps);
  const durationInFrames = Math.max(1, Math.round((end - start) * fps));

  return (
    <Sequence from={startFrame} durationInFrames={durationInFrames}>
      <StatInner
        text={text}
        subtext={subtext}
        brandColors={brandColors}
        fontFamily={fontFamily}
        durationInFrames={durationInFrames}
      />
    </Sequence>
  );
};

const StatInner: React.FC<{
  text: string;
  subtext?: string;
  brandColors: BrandColors;
  fontFamily: string;
  durationInFrames: number;
}> = ({ text, subtext, brandColors, fontFamily, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const popped = spring({
    frame,
    fps,
    from: 0,
    to: 1,
    config: { damping: 9, stiffness: 180, mass: 0.7 },
  });

  const scale = 0.4 + 0.6 * popped;

  const fadeOut = interpolate(
    frame,
    [Math.max(0, durationInFrames - 6), durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeOut,
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily,
            fontWeight: 900,
            fontSize: 360,
            lineHeight: 1,
            color: brandColors.keyword,
            WebkitTextStroke: `16px ${brandColors.stroke}`,
            paintOrder: "stroke fill",
            textShadow: "0 12px 32px rgba(0,0,0,0.55)",
            letterSpacing: "-0.02em",
          }}
        >
          {text}
        </div>
        {subtext ? (
          <div
            style={{
              marginTop: 24,
              fontFamily,
              fontWeight: 800,
              fontSize: 64,
              color: brandColors.normal,
              WebkitTextStroke: `8px ${brandColors.stroke}`,
              paintOrder: "stroke fill",
              textTransform: "uppercase",
              letterSpacing: "0.02em",
            }}
          >
            {subtext}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
