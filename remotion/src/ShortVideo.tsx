import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { ParkourBackground } from "./components/ParkourBackground";
import { DimOverlay } from "./components/DimOverlay";
import { CharacterOverlay } from "./components/CharacterOverlay";
import { SubtitleLayer } from "./components/SubtitleLayer";

export interface ScriptLine {
  character: "rick" | "morty";
  text: string;
  duration: number;
  emotion: string;
  audio_file?: string;
  startFrame: number;
  durationFrames: number;
}

export interface ShortVideoProps {
  lines: ScriptLine[];
  sessionId: string;
  totalDurationSec: number;
  footageFile: string;
}

export const ShortVideo: React.FC<ShortVideoProps> = ({
  lines,
  sessionId,
  footageFile,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <ParkourBackground file={footageFile} />
      <DimOverlay opacity={0.35} />

      {lines.map((line, i) => (
        <Sequence key={i} from={line.startFrame} durationInFrames={line.durationFrames}>
          <CharacterOverlay character={line.character} emotion={line.emotion} />
          {line.audio_file && (
            <Audio
              src={staticFile(`audio/${sessionId}/${line.audio_file}`)}
              volume={1}
            />
          )}
        </Sequence>
      ))}

      <SubtitleLayer lines={lines} />
    </AbsoluteFill>
  );
};
