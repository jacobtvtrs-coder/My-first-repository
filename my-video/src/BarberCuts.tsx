import React from "react";
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  staticFile,
} from "remotion";

// Before/after hard-cut edit: alternates AFTER and BEFORE shots, starting with
// a 0.1s strobe that slows down and ends on a held AFTER shot.
// Shot lengths (in frames at 30fps) were measured from the reference edit.
export const SHOT_FRAMES = [
  3,
  3,
  3,
  3,
  3,
  3,
  3,
  3,
  3,
  3, // strobe: 0.1s per shot
  4,
  4,
  4,
  5,
  5,
  5,
  5,
  5,
  6,
  7,
  7,
  8,
  9,
  12,
  13,
  15,
  12,
  18,
  34, // final hold on the finished cut
];

export const barberCutsDuration = SHOT_FRAMES.reduce((a, b) => a + b, 0);

export type BarberCutsProps = {
  // Video inside public/ (downloaded by scripts/fetch-footage.sh).
  footage: string;
  // Where in the footage each look starts, in seconds. Pick moments where the
  // head is at the same angle so only the hair seems to change.
  beforeStartSec: number;
  // Optional separate clip for the BEFORE shots (e.g. with the neck strip
  // painted out by scripts/remove-neck-strip.py). beforeStartSec is then
  // measured in this clip instead. Leave empty to use the main footage.
  beforeFootage: string;
  afterStartSec: number;
  // The only sound in the video: the footage itself stays muted.
  // Song lined up with the cuts (made by scripts/extract-reference-audio.sh).
  // Leave empty for no song.
  song: string;
  songVolume: number;
  // Look of the footage: 1 = unchanged. Lower brightness is darker;
  // a little extra contrast keeps the darker image crisp instead of muddy.
  brightness: number;
  contrast: number;
};

export const BarberCuts: React.FC<BarberCutsProps> = ({
  footage,
  beforeStartSec,
  beforeFootage,
  afterStartSec,
  song,
  songVolume,
  brightness,
  contrast,
}) => {
  const fps = 30;
  const src = staticFile(footage);
  const beforeSrc = beforeFootage ? staticFile(beforeFootage) : src;
  // Each look keeps playing from where it left off, instead of freezing.
  const played = { before: 0, after: 0 };
  let from = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <AbsoluteFill
        style={{ filter: `brightness(${brightness}) contrast(${contrast})` }}
      >
        {SHOT_FRAMES.map((frames, i) => {
          const look = i % 2 === 0 ? "after" : "before";
          const startSec = look === "after" ? afterStartSec : beforeStartSec;
          const trimBefore = Math.round(startSec * fps) + played[look];
          played[look] += frames;
          const start = from;
          from += frames;
          return (
            <Sequence key={i} from={start} durationInFrames={frames}>
              <OffthreadVideo
                src={look === "before" ? beforeSrc : src}
                trimBefore={trimBefore}
                muted
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </Sequence>
          );
        })}
      </AbsoluteFill>
      {song ? <Audio src={staticFile(song)} volume={songVolume} /> : null}
    </AbsoluteFill>
  );
};
