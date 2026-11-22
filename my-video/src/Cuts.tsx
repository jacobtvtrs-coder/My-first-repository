import React from "react";
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  useCurrentFrame,
} from "remotion";

// A vertical video made only of hard cuts: every shot starts instantly,
// with no transitions. Edit the list below to change words, colors and timing.

type ShotStyle = "word" | "circle" | "stripes" | "split" | "frame";

export type Shot = {
  text: string;
  bg: string;
  fg: string;
  frames: number;
  style: ShotStyle;
};

export type CutsProps = {
  shots: Shot[];
};

export const defaultShots: Shot[] = [
  { text: "CUT", bg: "#0B0B0F", fg: "#F5F5F0", frames: 24, style: "word" },
  { text: "TO", bg: "#FF3B30", fg: "#0B0B0F", frames: 16, style: "circle" },
  { text: "THE", bg: "#F5F5F0", fg: "#0B0B0F", frames: 14, style: "stripes" },
  { text: "BEAT", bg: "#2F5BFF", fg: "#F5F5F0", frames: 22, style: "frame" },
  { text: "FAST", bg: "#FFD60A", fg: "#0B0B0F", frames: 10, style: "split" },
  { text: "FASTER", bg: "#0B0B0F", fg: "#FFD60A", frames: 8, style: "word" },
  { text: "NOW", bg: "#FF3B30", fg: "#F5F5F0", frames: 6, style: "word" },
  { text: "STOP", bg: "#F5F5F0", fg: "#FF3B30", frames: 6, style: "circle" },
  { text: "GO", bg: "#2F5BFF", fg: "#FFD60A", frames: 6, style: "split" },
  { text: "NO", bg: "#0B0B0F", fg: "#F5F5F0", frames: 6, style: "stripes" },
  { text: "FADES", bg: "#FFD60A", fg: "#2F5BFF", frames: 14, style: "frame" },
  { text: "JUST", bg: "#0B0B0F", fg: "#F5F5F0", frames: 18, style: "word" },
  { text: "CUTS.", bg: "#FF3B30", fg: "#F5F5F0", frames: 60, style: "word" },
];

export const cutsDuration = (shots: Shot[]) =>
  shots.reduce((sum, s) => sum + s.frames, 0);

const FONT =
  "'Helvetica Neue', Helvetica, Arial Black, Arial, system-ui, sans-serif";

// Text size that keeps the word inside the 1080px-wide frame.
const fontSizeFor = (text: string) =>
  Math.min(420, Math.floor(1500 / Math.max(text.length, 2)));

const ShotView: React.FC<{ shot: Shot; index: number }> = ({ shot, index }) => {
  const frame = useCurrentFrame();
  const { text, bg, fg, frames, style } = shot;

  // Slow punch-in during the shot; the cut itself is instant.
  const zoom = interpolate(frame, [0, frames], [1, 1.12], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });
  // Alternate the drift direction so consecutive shots feel different.
  const drift = interpolate(frame, [0, frames], [0, index % 2 ? -30 : 30], {
    extrapolateRight: "clamp",
  });

  const word = (
    <div
      style={{
        fontFamily: FONT,
        fontWeight: 900,
        fontSize: fontSizeFor(text),
        letterSpacing: "-0.04em",
        lineHeight: 1,
        color: fg,
        transform: `translateY(${drift}px) scale(${zoom})`,
        textAlign: "center",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );

  return (
    <AbsoluteFill style={{ backgroundColor: bg }}>
      {style === "circle" && (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div
            style={{
              width: 900,
              height: 900,
              borderRadius: "50%",
              border: `40px solid ${fg}`,
              opacity: 0.25,
              transform: `scale(${zoom * 1.1})`,
            }}
          />
        </AbsoluteFill>
      )}
      {style === "stripes" && (
        <AbsoluteFill
          style={{
            backgroundImage: `repeating-linear-gradient(-30deg, ${fg}22 0 60px, transparent 60px 140px)`,
            backgroundPosition: `${frame * 12}px 0`,
          }}
        />
      )}
      {style === "split" && (
        <AbsoluteFill>
          <div style={{ height: "50%", backgroundColor: fg, opacity: 0.12 }} />
        </AbsoluteFill>
      )}
      {style === "frame" && (
        <AbsoluteFill style={{ padding: 70 }}>
          <div style={{ flex: 1, border: `14px solid ${fg}` }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        {word}
      </AbsoluteFill>
      {/* Shot counter in the corner, like a slate. */}
      <div
        style={{
          position: "absolute",
          bottom: 110,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 34,
          letterSpacing: "0.3em",
          color: fg,
          opacity: 0.6,
        }}
      >
        {String(index + 1).padStart(2, "0")}
      </div>
    </AbsoluteFill>
  );
};

export const Cuts: React.FC<CutsProps> = ({ shots }) => {
  let from = 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {shots.map((shot, i) => {
        const start = from;
        from += shot.frames;
        return (
          <Sequence key={i} from={start} durationInFrames={shot.frames}>
            <ShotView shot={shot} index={i} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
