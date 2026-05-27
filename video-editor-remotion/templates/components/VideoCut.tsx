import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  staticFile,
  useVideoConfig,
  interpolate,
} from "remotion";

export type VideoCutProps = {
  clip: string;
  sourceIn: number;
  sourceOut: number;
  cssFilter?: string;
  zoom?: number;
  yOffset?: number;
  audioFadeIn?: number;   // frames at start where audio ramps 0→1
  audioFadeOut?: number;  // frames at end where audio ramps 1→0
};

export const VideoCut: React.FC<VideoCutProps> = ({
  clip,
  sourceIn,
  sourceOut,
  cssFilter,
  zoom = 1.22,
  yOffset = -5,
  audioFadeIn = 2,
  audioFadeOut = 2,
}) => {
  const { fps } = useVideoConfig();
  const startFrom = Math.max(0, Math.round(sourceIn * fps));
  const endAt = Math.max(startFrom + 1, Math.round(sourceOut * fps));
  const durationFrames = endAt - startFrom;

  // Volume callback — ramps audio in at start of clip, out at end.
  // Crossfades adjacent cuts: end of clip N fades out while start of clip N+1 fades in.
  // If a cut has a TransitionSeries.Transition before/after, audioFadeIn/Out should
  // match the visual transition duration_frames.
  const volume = (frame: number) => {
    const fadeInProgress = audioFadeIn > 0
      ? interpolate(frame, [0, audioFadeIn], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        })
      : 1;
    const fadeOutProgress = audioFadeOut > 0
      ? interpolate(
          frame,
          [durationFrames - audioFadeOut, durationFrames],
          [1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        )
      : 1;
    return Math.min(fadeInProgress, fadeOutProgress);
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>
      <OffthreadVideo
        src={staticFile(`clips/${clip}`)}
        startFrom={startFrom}
        endAt={endAt}
        volume={volume}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `translateY(${yOffset}%) scale(${zoom})`,
          transformOrigin: "center center",
          filter: cssFilter ?? "none",
        }}
      />
    </AbsoluteFill>
  );
};
