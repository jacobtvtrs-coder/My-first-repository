import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";

// Beat-synced edit of the haircut clip. Picture only: no text or graphics.
// Every cut lands on a beat of the song; three section changes get a short
// punch-in zoom as the transition.
//
// The song is cut from the audio-source recording so that the video is exactly
// one loop of it (26.4475s): when Instagram replays the Reel, the music carries
// on seamlessly.

type Shot = {
  from: number; // first frame in the edit
  clipStartSec: number; // where in the clip this shot starts
  punchIn?: boolean; // zoom transition into this shot
};

// Frames at 30fps. Cut points are on beats of the song (strong hits where
// possible); each shot stays inside one camera shot of the original clip.
export const CLIP_EDIT_SHOTS: Shot[] = [
  { from: 0, clipStartSec: 0.0 }, // client in the chair, before
  { from: 46, clipStartSec: 1.55 }, // barber and client, wide
  { from: 118, clipStartSec: 4.1 }, // client touching his hair
  { from: 182, clipStartSec: 6.5, punchIn: true }, // fringe cutting starts
  { from: 251, clipStartSec: 9.05 }, // fringe close-up
  { from: 292, clipStartSec: 10.6 }, // top section, scissors
  { from: 398, clipStartSec: 14.43 }, // back of the head
  { from: 440, clipStartSec: 16.0 }, // nape cutting
  { from: 479, clipStartSec: 17.55, punchIn: true }, // product
  { from: 532, clipStartSec: 20.07 }, // styling, wide
  { from: 560, clipStartSec: 21.15, punchIn: true }, // finished look
  { from: 657, clipStartSec: 24.52 }, // final look, to the loop point
];

export const CLIP_EDIT_FRAMES = 793; // one loop of the song

export type ClipEditProps = {
  clip: string; // converted clip in public/
  song: string; // song in public/, already cut to one loop
};

const ShotVideo: React.FC<{
  src: string;
  clipStartSec: number;
  punchIn: boolean;
}> = ({ src, clipStartSec, punchIn }) => {
  const frame = useCurrentFrame();
  // Quick zoom from 108% to 100% over 8 frames, easing out.
  const scale = punchIn
    ? interpolate(frame, [0, 8], [1.08, 1], {
        extrapolateRight: "clamp",
        easing: Easing.out(Easing.cubic),
      })
    : 1;
  return (
    <OffthreadVideo
      src={src}
      trimBefore={Math.round(clipStartSec * 30)}
      muted
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        transform: `scale(${scale})`,
      }}
    />
  );
};

export const ClipEdit: React.FC<ClipEditProps> = ({ clip, song }) => {
  const src = staticFile(clip);
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {CLIP_EDIT_SHOTS.map((shot, i) => {
        const end =
          i + 1 < CLIP_EDIT_SHOTS.length
            ? CLIP_EDIT_SHOTS[i + 1].from
            : CLIP_EDIT_FRAMES;
        return (
          <Sequence key={i} from={shot.from} durationInFrames={end - shot.from}>
            <ShotVideo
              src={src}
              clipStartSec={shot.clipStartSec}
              punchIn={Boolean(shot.punchIn)}
            />
          </Sequence>
        );
      })}
      <Audio src={staticFile(song)} />
    </AbsoluteFill>
  );
};
