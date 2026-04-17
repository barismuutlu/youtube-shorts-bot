import React, { useEffect } from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, staticFile } from "remotion";
import { ScriptLine } from "../ShortVideo";

// Bangers fontunu yükle
if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.textContent = `@font-face { font-family: 'Bangers'; src: url('${staticFile("fonts/Bangers-Regular.ttf")}') format('truetype'); }`;
  document.head.appendChild(style);
}

interface Props {
  lines: ScriptLine[];
}

export const SubtitleLayer: React.FC<Props> = ({ lines }) => {
  const frame = useCurrentFrame();

  const active = lines.find(
    (l) => frame >= l.startFrame && frame < l.startFrame + l.durationFrames
  );

  if (!active) return null;

  const fadeIn = interpolate(
    frame,
    [active.startFrame, active.startFrame + 4],
    [0, 1],
    { extrapolateRight: "clamp" }
  );

  const color = active.character === "rick" ? "#00FF88" : "#FFD700";

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        top: "42%",
        bottom: "auto",
        height: "auto",
        position: "absolute",
        left: 0,
        right: 0,
        opacity: fadeIn,
      }}
    >
      <div
        style={{
          fontFamily: "Bangers, Impact, sans-serif",
          fontSize: 72,
          color: "white",
          WebkitTextStroke: "4px black",
          textAlign: "center",
          padding: "0 40px",
          lineHeight: 1.2,
          textShadow: "3px 3px 6px rgba(0,0,0,0.8)",
        }}
      >
        <span style={{ color }}>{active.character.toUpperCase()}: </span>
        {active.text}
      </div>
    </AbsoluteFill>
  );
};
