import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import {
  TransitionSeries,
  linearTiming,
  springTiming,
} from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";
import { clockWipe } from "@remotion/transitions/clock-wipe";

// TransitionScene — drop-in transition between two children rendered at the same overlay slot.
// Replaces hard cuts in v1 narrative segments. Auto-routes presentation kind to the matching
// Remotion preset and wires duration to the Series.Sequence frames.
//
// Plan usage:
//   { "kind": "transition_scene", "presentation": "slide", "direction": "from-right",
//     "duration_ms": 400, "from_text": "ANTES", "to_text": "DEPOIS" }

type Presentation = "fade" | "slide" | "wipe" | "flip" | "clock-wipe";

const buildPresentation = (
  kind: Presentation,
  direction: "from-left" | "from-right" | "from-top" | "from-bottom",
  width: number,
  height: number,
) => {
  switch (kind) {
    case "fade":
      return fade();
    case "slide":
      return slide({ direction });
    case "wipe":
      return wipe({ direction });
    case "flip":
      return flip({ direction });
    case "clock-wipe":
      return clockWipe({ width, height });
  }
};

const Card: React.FC<{ text: string; bg: string; fg: string }> = ({ text, bg, fg }) => (
  <AbsoluteFill style={{
    background: bg, color: fg, display: "flex",
    alignItems: "center", justifyContent: "center",
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: 110, fontWeight: 900, letterSpacing: 3,
  }}>
    {text}
  </AbsoluteFill>
);

export type TransitionSceneProps = {
  startFrame: number;
  endFrame: number;
  presentation?: Presentation;
  direction?: "from-left" | "from-right" | "from-top" | "from-bottom";
  duration_ms?: number;
  from_text: string;
  to_text: string;
  from_bg?: string;
  to_bg?: string;
  from_fg?: string;
  to_fg?: string;
};

export const TransitionScene: React.FC<TransitionSceneProps> = ({
  startFrame, endFrame,
  presentation = "fade",
  direction = "from-right",
  duration_ms = 400,
  from_text, to_text,
  from_bg = "#0A0A0A", to_bg = "#1F4D2C",
  from_fg = "#F5F1E8", to_fg = "#F5F1E8",
}) => {
  const { fps, width, height } = useVideoConfig();
  const total = Math.max(1, endFrame - startFrame);
  const transitionFrames = Math.max(1, Math.round((duration_ms / 1000) * fps));
  const half = Math.max(1, Math.floor((total - transitionFrames) / 2));

  return (
    <AbsoluteFill>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={half}>
          <Card text={from_text} bg={from_bg} fg={from_fg} />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={buildPresentation(presentation, direction, width, height)}
          timing={linearTiming({ durationInFrames: transitionFrames })}
        />
        <TransitionSeries.Sequence durationInFrames={total - half - transitionFrames}>
          <Card text={to_text} bg={to_bg} fg={to_fg} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};

// Convenience helper — exposes spring-timed transition for "snappier" feel between scenes.
export const useTransitionTiming = (kind: "linear" | "spring" = "linear", frames = 12) =>
  kind === "spring"
    ? springTiming({ config: { damping: 200 } })
    : linearTiming({ durationInFrames: frames });
