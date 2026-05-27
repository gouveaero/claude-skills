import React from "react";
import {
  AbsoluteFill,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import {
  classifyWord,
  DEFAULT_BRAND_COLORS,
  DEFAULT_EMPHASIS_WORDS,
  SAFE_ZONES_INSTAGRAM_REEL,
  easings,
  type BrandColors,
} from "./helpers";

export type CaptionWord = {
  text: string;
  start: number;
  end: number;
  emphasis?: "keyword" | "emphasis" | "normal";
};

export type KineticCaptionProps = {
  // Either provide `words` (preferred — for word-by-word reveal) or fall back to `text`+(start,end)
  words?: CaptionWord[];
  text?: string;
  start: number;
  end: number;
  style?: "highlight_accent" | "highlight_box" | "minimal";
  brandColors?: BrandColors;
  emphasisWords?: Set<string>;
  fontFamily?: string;
};

export const KineticCaption: React.FC<KineticCaptionProps> = ({
  words,
  text,
  start,
  end,
  style = "highlight_accent",
  brandColors = DEFAULT_BRAND_COLORS,
  emphasisWords = DEFAULT_EMPHASIS_WORDS,
  fontFamily = "Inter, system-ui, sans-serif",
}) => {
  const { fps } = useVideoConfig();
  const startFrame = Math.round(start * fps);
  const durationInFrames = Math.max(1, Math.round((end - start) * fps));

  // Fallback: if no words array, build one from text with even time distribution
  const wordList: CaptionWord[] =
    words && words.length > 0
      ? words
      : (text ?? "")
          .split(/\s+/)
          .filter(Boolean)
          .map((w, i, arr) => {
            const dur = end - start;
            const slice = dur / arr.length;
            return { text: w, start: start + i * slice, end: start + (i + 1) * slice };
          });

  return (
    <Sequence from={startFrame} durationInFrames={durationInFrames}>
      <CaptionInner
        words={wordList}
        absStart={start}
        style={style}
        brandColors={brandColors}
        emphasisWords={emphasisWords}
        fontFamily={fontFamily}
        durationInFrames={durationInFrames}
      />
    </Sequence>
  );
};

const CaptionInner: React.FC<{
  words: CaptionWord[];
  absStart: number;
  style: "highlight_accent" | "highlight_box" | "minimal";
  brandColors: BrandColors;
  emphasisWords: Set<string>;
  fontFamily: string;
  durationInFrames: number;
}> = ({ words, absStart, style, brandColors, emphasisWords, fontFamily, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentSec = absStart + frame / fps;

  // Caption-level pop-in
  const popIn = spring({
    frame, fps, from: 0, to: 1,
    config: { damping: 14, stiffness: 220, mass: 0.5 },
  });
  const fadeOut = interpolate(
    frame,
    [Math.max(0, durationInFrames - 4), durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        // Captions higher in frame — above Instagram bottom UI but in lower-third
        paddingBottom: SAFE_ZONES_INSTAGRAM_REEL.bottom + 340,
        opacity: fadeOut * popIn,
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "baseline",
          gap: "0.55em",
          maxWidth: "82%",
          textAlign: "center",
        }}
      >
        {words.map((w, i) => {
          const cls = w.emphasis ?? classifyWord(w.text, emphasisWords);

          // Word state — past / active / future
          const ACTIVE_PAD = 0.06; // 60ms pre/post leeway
          const isActive = currentSec >= w.start - ACTIVE_PAD && currentSec <= w.end + ACTIVE_PAD;
          const isPast = currentSec > w.end + ACTIVE_PAD;

          // Per-class easing on word entry
          // keyword (numbers/%) → outBack (overshoot, snappy bounce)
          // emphasis (AGIOTA, SELIC...) → outCubic (clean, fast settle)
          // normal → inOutQuad (suave, no surprises)
          const easingFn = cls === "keyword"
            ? easings.outBack
            : cls === "emphasis"
              ? easings.outCubic
              : easings.inOutQuad;

          const wordProgress = interpolate(
            currentSec,
            [w.start - 0.08, w.start + 0.10],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easingFn }
          );
          // Different target scale per class — keyword pops harder
          const targetScale = cls === "keyword" ? 1.22 : cls === "emphasis" ? 1.14 : 1.06;
          const activeScale = isActive ? 1.0 + (targetScale - 1.0) * wordProgress : 1.0;

          // Smaller font sizes — addresses "fica muito grande"
          const fontSize = cls === "keyword" ? 84 : cls === "emphasis" ? 76 : 68;
          const fontWeight = 900;

          // Active styling
          const useBox = isActive && (cls === "keyword" || cls === "emphasis" || style === "highlight_box");
          const textColor = useBox ? "#0A0A0A" : (isActive && cls === "keyword" ? brandColors.keyword : "#FFFFFF");
          const bgColor = useBox
            ? (cls === "keyword" ? brandColors.keyword : brandColors.emphasis)
            : "transparent";

          // Opacity: active=1, past=0.55, future=0.45
          const opacity = isActive ? 1 : isPast ? 0.55 : 0.45;

          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                transform: `scale(${activeScale})`,
                transformOrigin: "center center",
                fontFamily,
                fontWeight,
                fontSize,
                color: textColor,
                background: bgColor,
                padding: useBox ? "0.04em 0.20em" : 0,
                borderRadius: 14,
                lineHeight: 1.1,
                letterSpacing: "0.005em",
                WebkitTextStroke: useBox ? "0" : `9px ${brandColors.stroke}`,
                paintOrder: "stroke fill",
                textShadow: useBox
                  ? "0 4px 12px rgba(0,0,0,0.4)"
                  : "0 4px 12px rgba(0,0,0,0.5)",
                opacity,
                transition: "none",
              }}
            >
              {w.text.toUpperCase()}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
