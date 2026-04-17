import React from "react";
import {
  AbsoluteFill,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  spring,
} from "remotion";

interface Props {
  character: "rick" | "morty";
  emotion: string;
}

export const CharacterOverlay: React.FC<Props> = ({ character, emotion }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isTalking = emotion !== "idle";

  // Konuşma bobbing animasyonu
  const bobY = spring({
    frame: frame % 12,
    fps,
    from: 0,
    to: isTalking ? -10 : 0,
    durationInFrames: 6,
    config: { damping: 8 },
  });

  const imgSrc = staticFile(`characters/${character}.png`);

  const isRick = character === "rick";

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "flex-end",
        flexDirection: "row",
        bottom: 0,
        top: "auto",
        height: "auto",
        position: "absolute",
        left: isRick ? 10 : undefined,
        right: isRick ? undefined : 10,
        bottom: 80,
        transform: `translateY(${bobY}px)`,
      }}
    >
      <Img
        src={imgSrc}
        style={{
          height: 700,
          objectFit: "contain",
          // Morty'yi yatay çevir
          transform: isRick ? "none" : "scaleX(-1)",
        }}
      />
    </AbsoluteFill>
  );
};
