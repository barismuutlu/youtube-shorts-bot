import React from "react";
import { AbsoluteFill, Loop, Video, staticFile, useVideoConfig } from "remotion";

// Loop için sabit bir segment uzunluğu (300 frame = 10sn @ 30fps)
// Asıl footage daha uzunsa sorun yok; daha kısaysa tekrar başlar
const LOOP_SEGMENT_FRAMES = 300;

export const ParkourBackground: React.FC<{ file: string }> = ({ file }) => {
  const { durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill>
      <Loop durationInFrames={LOOP_SEGMENT_FRAMES}>
        <Video
          src={staticFile(`footage/${file}`)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
          durationInFrames={durationInFrames}
        />
      </Loop>
    </AbsoluteFill>
  );
};
