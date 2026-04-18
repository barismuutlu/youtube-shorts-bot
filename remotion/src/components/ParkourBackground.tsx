import React from "react";
import { AbsoluteFill, Video, staticFile } from "remotion";

export const ParkourBackground: React.FC<{ file: string }> = ({ file }) => {
  return (
    <AbsoluteFill>
      <Video
        src={staticFile(`footage/${file}`)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
        loop
      />
    </AbsoluteFill>
  );
};
