import React from "react";
import { Composition } from "remotion";
import { SavedSounds, DURATION } from "./SavedSounds";

export const Root: React.FC = () => (
  <Composition
    id="SavedSounds"
    component={SavedSounds}
    durationInFrames={DURATION}
    fps={30}
    width={1080}
    height={1920}
  />
);
