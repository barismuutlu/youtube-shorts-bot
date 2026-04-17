import React from "react";
import { AbsoluteFill } from "remotion";

export const DimOverlay: React.FC<{ opacity: number }> = ({ opacity }) => (
  <AbsoluteFill
    style={{ backgroundColor: `rgba(0, 0, 0, ${opacity})` }}
  />
);
