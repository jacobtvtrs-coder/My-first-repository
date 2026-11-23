import "@fontsource/montserrat/800.css";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import type { CalculateMetadataFunction } from "remotion";

// Edit of the barbershop conversation. The shot list and subtitles live in
// public/footage/vlog/edit.json (made from the transcript, kept out of git
// because it is a private conversation). Picture comes from the converted
// clips in public/footage/vlog/, sound from the cleaned audio in
// public/footage/vlog-audio/ (background noise removed between speech).

export const FPS = 30;
const TRANSITION_FRAMES = 8;

type Zoom = "none" | "in" | "out" | "punch";
type Transition = "cut" | "fade" | "slide";

export type Segment = {
  clip: string; // e.g. "IMG_3065"
  inSec: number;
  outSec: number;
  zoom?: Zoom;
  focus?: string; // transform-origin for zooms, e.g. "50% 35%"
  transition?: Transition; // how this shot comes in
  mute?: boolean;
};

export type Word = { start: number; end: number; word: string };
export type Caption = { start: number; end: number; words: Word[] };

export type VlogEditProps = {
  segments: Segment[];
  // Subtitles per clip, in that clip's own time.
  captions: Record<string, Caption[]>;
};

export const loadVlogEdit: CalculateMetadataFunction<
  VlogEditProps
> = async () => {
  const data: VlogEditProps = await fetch(
    staticFile("footage/vlog/edit.json"),
  ).then((r) => r.json());
  const frames = data.segments.reduce(
    (sum, s) => sum + Math.round((s.outSec - s.inSec) * FPS),
    0,
  );
  const overlaps =
    data.segments.filter(
      (s, i) => i > 0 && s.transition && s.transition !== "cut",
    ).length * TRANSITION_FRAMES;
  return { props: data, durationInFrames: frames - overlaps };
};

const Subtitle: React.FC<{ captions: Caption[]; clipSec: number }> = ({
  captions,
  clipSec,
}) => {
  const cap = captions.find((c) => clipSec >= c.start && clipSec < c.end);
  if (!cap) return null;
  // Gentle pop when a new line appears.
  const age = clipSec - cap.start;
  const pop = interpolate(age, [0, 0.12], [0.92, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.back(2)),
  });
  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 430,
      }}
    >
      <div
        style={{
          maxWidth: 900,
          textAlign: "center",
          fontFamily: "Montserrat",
          fontWeight: 800,
          fontSize: 66,
          lineHeight: 1.15,
          letterSpacing: "-0.01em",
          transform: `scale(${pop})`,
          textShadow:
            "0 4px 18px rgba(0,0,0,0.55), 0 0 3px rgba(0,0,0,0.9), 0 2px 2px rgba(0,0,0,0.6)",
        }}
      >
        {cap.words.map((w, i) => {
          const active = clipSec >= w.start && clipSec < w.end + 0.05;
          const said = clipSec >= w.start;
          return (
            <span
              key={i}
              style={{
                color: active ? "#FFD84D" : "#FFFFFF",
                opacity: said ? 1 : 0.55,
              }}
            >
              {w.word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Shot: React.FC<{ seg: Segment; captions: Caption[] }> = ({
  seg,
  captions,
}) => {
  const frame = useCurrentFrame();
  const frames = Math.round((seg.outSec - seg.inSec) * FPS);
  const p = Math.min(1, frame / Math.max(1, frames - 1));
  const ease = Easing.inOut(Easing.quad)(p);
  const scale =
    seg.zoom === "in"
      ? 1 + 0.14 * ease
      : seg.zoom === "out"
        ? 1.14 - 0.14 * ease
        : seg.zoom === "punch"
          ? 1.32
          : 1;
  const clipSec = seg.inSec + frame / FPS;
  const src = `footage/vlog/${seg.clip}`;
  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>
      <OffthreadVideo
        src={staticFile(`${src}.mp4`)}
        trimBefore={Math.round(seg.inSec * FPS)}
        muted
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
          transformOrigin: seg.focus ?? "50% 40%",
        }}
      />
      {seg.mute ? null : (
        <Audio
          src={staticFile(`footage/vlog-audio/${seg.clip}.clean.wav`)}
          trimBefore={Math.round(seg.inSec * FPS)}
        />
      )}
      <Subtitle captions={captions} clipSec={clipSec} />
    </AbsoluteFill>
  );
};

export const VlogEdit: React.FC<VlogEditProps> = ({ segments, captions }) => {
  if (!segments?.length) return <AbsoluteFill style={{ background: "#000" }} />;
  return (
    <TransitionSeries>
      {segments.flatMap((seg, i) => {
        const frames = Math.round((seg.outSec - seg.inSec) * FPS);
        const items: React.ReactNode[] = [];
        if (i > 0 && seg.transition && seg.transition !== "cut") {
          items.push(
            <TransitionSeries.Transition
              key={`t${i}`}
              presentation={
                seg.transition === "slide"
                  ? slide({ direction: "from-right" })
                  : fade()
              }
              timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
            />,
          );
        }
        items.push(
          <TransitionSeries.Sequence key={`s${i}`} durationInFrames={frames}>
            <Shot seg={seg} captions={captions[seg.clip] ?? []} />
          </TransitionSeries.Sequence>,
        );
        return items;
      })}
    </TransitionSeries>
  );
};
