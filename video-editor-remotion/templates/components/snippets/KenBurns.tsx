import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, Img } from "remotion";

interface KenBurnsProps {
  src: string;
  durationFrames?: number;
  zoomFrom?: number;
  zoomTo?: number;
  panX?: number; // px deslocamento horizontal
  panY?: number; // px deslocamento vertical
}

export const KenBurns: React.FC<KenBurnsProps> = ({
  src,
  durationFrames = 150,
  zoomFrom = 1.0,
  zoomTo = 1.15,
  panX = 0,
  panY = -20,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const progress = Math.min(frame / durationFrames, 1);
  const scale = interpolate(progress, [0, 1], [zoomFrom, zoomTo]);
  const translateX = interpolate(progress, [0, 1], [0, panX]);
  const translateY = interpolate(progress, [0, 1], [0, panY]);

  return (
    <div style={{ width, height, overflow: "hidden", position: "relative" }}>
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
          transformOrigin: "center center",
        }}
      />
    </div>
  );
};
