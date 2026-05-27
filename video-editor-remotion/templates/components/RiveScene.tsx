import React from "react";
import {
  AbsoluteFill,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { RemotionRiveCanvas } from "@remotion/rive";

// RiveScene — embed a Rive `.riv` interactive vector animation.
// Rive is more lightweight than Lottie for interactive UI animations and has better
// support for state machines (e.g. progress-driven animations).
//
// Plan usage:
//   { "kind": "rive", "rive_src": "rive/loader.riv",
//     "artboard": "Main", "state_machine": "State Machine 1",
//     "position": "center", "size": 600 }
//
// Place .riv files in <remotion>/public/rive/ before render.

export type RiveSceneProps = {
  startFrame: number;
  endFrame: number;
  rive_src: string;
  artboard?: string;
  state_machine?: string;
  position?: "center" | "top-right" | "top-left" | "bottom-right" | "bottom-left";
  size?: number;
};

export const RiveScene: React.FC<RiveSceneProps> = ({
  startFrame, endFrame, rive_src,
  artboard, state_machine,
  position = "center", size = 600,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const dur = endFrame - startFrame;
  const local = frame - startFrame;
  const fadeIn = interpolate(local, [0, fps * 0.3], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = local > dur - fps * 0.3
    ? interpolate(local, [dur - fps * 0.3, dur], [1, 0])
    : 1;
  const op = Math.min(fadeIn, fadeOut);

  const posStyle: React.CSSProperties =
    position === "center" ? { left: "50%", top: "50%", transform: "translate(-50%, -50%)" } :
    position === "top-right" ? { top: 80, right: 60 } :
    position === "top-left" ? { top: 80, left: 60 } :
    position === "bottom-right" ? { bottom: 80, right: 60 } :
    { bottom: 80, left: 60 };

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
      <div style={{ position: "absolute", width: size, height: size, ...posStyle }}>
        <RemotionRiveCanvas
          src={staticFile(rive_src)}
          artboard={artboard}
          stateMachines={state_machine ? [state_machine] : undefined}
        />
      </div>
    </AbsoluteFill>
  );
};
