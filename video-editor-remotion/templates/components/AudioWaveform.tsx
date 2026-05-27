import React from "react";
import {
  AbsoluteFill,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { useAudioData, visualizeAudio } from "@remotion/media-utils";

// AudioWaveform — vertical bars reacting to the audio at the current frame.
// Drives off the narration TTS or background music. Useful for music videos and
// aviation reels (Vhoe — engine frequency visualization).
//
// Plan usage:
//   { "kind": "audio_waveform", "audio_src": "voice.mp3", "bars": 48,
//     "color": "#B87333", "position": "bottom", "height_px": 200,
//     "smoothing": 0.7, "frequency_range": "full" }
//
// audio_src is resolved against public/. Place files there before render.

export type AudioWaveformProps = {
  startFrame: number;
  endFrame: number;
  audio_src: string;
  bars?: number;
  color?: string;
  position?: "top" | "bottom" | "center";
  height_px?: number;
  smoothing?: number;
  frequency_range?: "full" | "voice" | "bass";
};

const FREQ_RANGES: Record<string, { lo: number; hi: number }> = {
  full: { lo: 0, hi: 1 },
  voice: { lo: 0.1, hi: 0.5 },
  bass: { lo: 0, hi: 0.2 },
};

export const AudioWaveform: React.FC<AudioWaveformProps> = ({
  startFrame, endFrame,
  audio_src,
  bars = 48,
  color = "#B87333",
  position = "bottom",
  height_px = 200,
  smoothing = 0.7,
  frequency_range = "full",
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const audioData = useAudioData(staticFile(audio_src));

  if (!audioData) return null;

  const dur = endFrame - startFrame;
  const local = frame - startFrame;
  const fadeIn = interpolate(local, [0, fps * 0.3], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = local > dur - fps * 0.3
    ? interpolate(local, [dur - fps * 0.3, dur], [1, 0])
    : 1;
  const op = Math.min(fadeIn, fadeOut);

  const samples = visualizeAudio({
    fps,
    frame,
    audioData,
    numberOfSamples: bars * 2,
    smoothing,
  });

  // Slice to the requested frequency range
  const { lo, hi } = FREQ_RANGES[frequency_range] ?? FREQ_RANGES.full;
  const rangedSamples = samples.slice(
    Math.floor(samples.length * lo),
    Math.ceil(samples.length * hi),
  ).slice(0, bars);

  const barWidth = width / bars;
  const gap = barWidth * 0.25;
  const drawWidth = barWidth - gap;

  const containerStyle: React.CSSProperties =
    position === "bottom" ? { bottom: 0, top: "auto" } :
    position === "top" ? { top: 0, bottom: "auto" } :
    { top: "50%", transform: "translateY(-50%)" };

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
      <div style={{
        position: "absolute", left: 0, right: 0, height: height_px,
        display: "flex", alignItems: "flex-end", justifyContent: "space-around",
        ...containerStyle,
      }}>
        {rangedSamples.map((amp, i) => {
          const h = Math.max(4, Math.min(height_px, amp * height_px * 3));
          return (
            <div key={i} style={{
              width: drawWidth, height: h,
              background: color, borderRadius: drawWidth / 2,
              transform: position === "top" ? "translateY(0)" : undefined,
              transformOrigin: position === "top" ? "top" : "bottom",
              boxShadow: `0 0 ${h * 0.2}px ${color}66`,
            }} />
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
