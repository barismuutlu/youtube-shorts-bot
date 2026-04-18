import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";

interface Props {
  character: "rick" | "morty";
  emotion: string;
}

export const CharacterOverlay: React.FC<Props> = ({ character }) => {
  const imgSrc = staticFile(`characters/${character}.png`);

  const isRick = character === "rick";

  return (
    <AbsoluteFill
      style={{
        top: "auto",
        height: "auto",
        bottom: 80,
        left: isRick ? 10 : undefined,
        right: isRick ? undefined : 10,
      }}
    >
      <Img
        src={imgSrc}
        style={{
          height: 700,
          objectFit: "contain",
          transform: isRick ? "none" : "scaleX(-1)",
        }}
      />
    </AbsoluteFill>
  );
};
