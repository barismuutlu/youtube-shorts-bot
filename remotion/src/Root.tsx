import React from "react";
import { Composition } from "remotion";
import { ShortVideo, ShortVideoProps } from "./ShortVideo";

export const RemotionRoot: React.FC = () => {
  const defaultProps: ShortVideoProps = {
    lines: [],
    sessionId: "test",
    totalDurationSec: 45,
    footageFile: "parkour_001.mp4",
  };

  return (
    <Composition
      id="ShortVideo"
      component={ShortVideo}
      durationInFrames={1740}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={defaultProps}
      calculateMetadata={({ props }) => ({
        durationInFrames: Math.round(props.totalDurationSec * 30),
      })}
    />
  );
};
