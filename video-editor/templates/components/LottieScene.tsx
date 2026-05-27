import React from "react";
import {
  AbsoluteFill,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  delayRender,
  continueRender,
  cancelRender,
  interpolate,
} from "remotion";
import { Lottie, LottieAnimationData } from "@remotion/lottie";

// LottieScene — embed an After-Effects Lottie animation as an overlay.
// Lottie playback is driven by Remotion's timeline automatically (no manual frame math
// needed for the inner animation). We add a fade-in/out at the wrapper level.
//
// Plan usage:
//   { "kind": "lottie", "lottie_src": "animations/logo-reveal.json",
//     "position": "center", "scale": 1.0, "loop": false }
//
// Place .json (or .lottie) files in <remotion>/public/animations/ before render.

export type LottieSceneProps = {
  startFrame: number;
  endFrame: number;
  lottie_src: string;
  position?: "center" | "top-right" | "top-left" | "bottom-right" | "bottom-left";
  scale?: number;
  loop?: boolean;
};

export const LottieScene: React.FC<LottieSceneProps> = ({
  startFrame, endFrame, lottie_src,
  position = "center", scale = 1, loop = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [data, setData] = React.useState<LottieAnimationData | null>(null);
  const [handle] = React.useState(() => delayRender(`lottie:${lottie_src}`));

  React.useEffect(() => {
    fetch(staticFile(lottie_src))
      .then((r) => r.json())
      .then((json: LottieAnimationData) => {
        setData(json);
        continueRender(handle);
      })
      .catch((err) => cancelRender(err));
  }, [lottie_src, handle]);

  if (!data) return null;

  const dur = endFrame - startFrame;
  const local = frame - startFrame;
  const fadeIn = interpolate(local, [0, fps * 0.3], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = local > dur - fps * 0.3
    ? interpolate(local, [dur - fps * 0.3, dur], [1, 0])
    : 1;
  const op = Math.min(fadeIn, fadeOut);

  const posStyle: React.CSSProperties =
    position === "center" ? { left: "50%", top: "50%", transform: `translate(-50%, -50%) scale(${scale})` } :
    position === "top-right" ? { top: 80, right: 60, transform: `scale(${scale})` } :
    position === "top-left" ? { top: 80, left: 60, transform: `scale(${scale})` } :
    position === "bottom-right" ? { bottom: 80, right: 60, transform: `scale(${scale})` } :
    { bottom: 80, left: 60, transform: `scale(${scale})` };

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
      <div style={{ position: "absolute", ...posStyle }}>
        <Lottie animationData={data} loop={loop} />
      </div>
    </AbsoluteFill>
  );
};
