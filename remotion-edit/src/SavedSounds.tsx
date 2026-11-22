import React from "react";
import {
  AbsoluteFill, OffthreadVideo, Easing, interpolate, spring,
  staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { useAudioData, visualizeAudio } from "@remotion/media-utils";

const CLIP = staticFile("clip.mp4");
const CLIP_SECONDS = 30;
export const DURATION = CLIP_SECONDS * 30; // 900 frames @ 30fps

const ACCENT_A = "#ff3d77";
const ACCENT_B = "#7b5cff";
const ACCENT_C = "#ffb03a";

// Source is 1528x1080 (landscape). Crop to the list area: x 110..1270.
const SRC_W = 1528;
const SRC_H = 1080;
const CROP_X = 110;
const CROP_W = 1160;
const CARD_W = 960;
const SCALE = CARD_W / CROP_W;
const CARD_H = Math.round(SRC_H * SCALE); // 894
const CARD_TOP = 380;

const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const a = frame * 0.6;
  return (
    <AbsoluteFill style={{ background: "#07070c" }}>
      <AbsoluteFill style={{ filter: "blur(60px) saturate(1.4)", opacity: 0.35, transform: "scale(1.3)" }}>
        <OffthreadVideo src={CLIP} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${50 + 30 * Math.sin(a / 60)}% ${20 + 10 * Math.cos(a / 50)}%, ${ACCENT_A}55, transparent 45%),
                       radial-gradient(circle at ${50 - 30 * Math.sin(a / 70)}% ${85 + 8 * Math.sin(a / 40)}%, ${ACCENT_B}66, transparent 50%)`,
        }}
      />
    </AbsoluteFill>
  );
};

const Title: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = ["SAVED", "SOUNDS"];
  const sub = interpolate(frame, [22, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 110, width: "100%", textAlign: "center", fontFamily: "Inter, Helvetica, Arial, sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "center", gap: 28 }}>
        {words.map((w, i) => {
          const s = spring({ frame: frame - i * 6, fps, config: { damping: 12, mass: 0.6 } });
          return (
            <span
              key={w}
              style={{
                fontSize: 112, fontWeight: 900, letterSpacing: -2, color: "white",
                transform: `translateY(${(1 - s) * 80}px) scale(${0.8 + 0.2 * s})`, opacity: s,
                background: i === 1 ? `linear-gradient(90deg, ${ACCENT_A}, ${ACCENT_C})` : undefined,
                WebkitBackgroundClip: i === 1 ? "text" : undefined,
                WebkitTextFillColor: i === 1 ? "transparent" : undefined,
              }}
            >
              {w}
            </span>
          );
        })}
      </div>
      <div style={{ marginTop: 6, fontSize: 38, fontWeight: 600, color: "#ffffffcc", letterSpacing: 6, opacity: sub, transform: `translateY(${(1 - sub) * 20}px)` }}>
        10 TRACKS · ON REPEAT
      </div>
    </div>
  );
};

const Card: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - 8, fps, config: { damping: 14 } });
  const zoom = interpolate(frame, [0, DURATION], [1, 1.06]);
  const tilt = interpolate(enter, [0, 1], [12, 0]);
  // glare sweep every 6 seconds
  const sweep = ((frame % 180) / 180) * 2.4 - 0.7;
  return (
    <div
      style={{
        position: "absolute", left: (1080 - CARD_W) / 2, top: CARD_TOP, width: CARD_W, height: CARD_H,
        borderRadius: 48, overflow: "hidden",
        boxShadow: `0 40px 120px #000c, 0 0 0 3px #ffffff22, 0 0 80px ${ACCENT_B}55`,
        transform: `perspective(1600px) rotateX(${tilt}deg) translateY(${(1 - enter) * 500}px) scale(${zoom})`,
        opacity: enter,
      }}
    >
      <OffthreadVideo
        src={CLIP}
        style={{ position: "absolute", width: SRC_W * SCALE, height: CARD_H, left: -CROP_X * SCALE, top: 0, maxWidth: "none" }}
        volume={(f) => interpolate(f, [0, 15, DURATION - 40, DURATION], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
      />
      <AbsoluteFill
        style={{
          background: `linear-gradient(115deg, transparent ${sweep * 100 - 10}%, #ffffff18 ${sweep * 100}%, transparent ${sweep * 100 + 10}%)`,
          pointerEvents: "none",
        }}
      />
    </div>
  );
};

const Visualizer: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const audio = useAudioData(CLIP);
  const BARS = 48;
  const values = audio
    ? visualizeAudio({ fps, frame, audioData: audio, numberOfSamples: 64, smoothing: true }).slice(0, BARS)
    : new Array(BARS).fill(0);
  const appear = interpolate(frame, [25, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const top = CARD_TOP + CARD_H + 170;
  return (
    <div style={{ position: "absolute", top, left: 90, right: 90, height: 260, display: "flex", alignItems: "center", gap: 6, opacity: appear }}>
      {values.map((v, i) => {
        const boosted = Math.min(1, Math.pow(v * (1 + i / 8), 0.6) * 1.6);
        const h = 12 + boosted * 240;
        return (
          <div
            key={i}
            style={{
              flex: 1, height: h, borderRadius: 999,
              background: `linear-gradient(180deg, ${ACCENT_C}, ${ACCENT_A} 50%, ${ACCENT_B})`,
              boxShadow: `0 0 ${10 + boosted * 20}px ${ACCENT_A}88`,
            }}
          />
        );
      })}
    </div>
  );
};

const NowPlaying: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 35, fps, config: { damping: 14 } });
  const pulse = 0.6 + 0.4 * Math.abs(Math.sin(frame / 8));
  return (
    <div
      style={{
        position: "absolute", top: CARD_TOP + CARD_H + 40, left: 0, right: 0, display: "flex", justifyContent: "center",
        opacity: s, transform: `translateY(${(1 - s) * 40}px)`, fontFamily: "Inter, Helvetica, Arial, sans-serif",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "16px 30px", borderRadius: 999, background: "#ffffff14", border: "2px solid #ffffff26", color: "white" }}>
        <div style={{ width: 16, height: 16, borderRadius: 8, background: ACCENT_A, boxShadow: `0 0 ${20 * pulse}px ${ACCENT_A}`, opacity: pulse }} />
        <span style={{ fontSize: 24, fontWeight: 800, letterSpacing: 4, color: "#ffffffaa" }}>NOW PLAYING</span>
        <span style={{ fontSize: 32, fontWeight: 700 }}>Talk To You</span>
        <span style={{ fontSize: 28, color: "#ffffff99" }}>ANOTR, 54 Ultra</span>
      </div>
    </div>
  );
};

const Progress: React.FC = () => {
  const frame = useCurrentFrame();
  const p = frame / DURATION;
  const fmt = (s: number) => `0:${String(Math.floor(s)).padStart(2, "0")}`;
  return (
    <div style={{ position: "absolute", bottom: 90, left: 90, right: 90, fontFamily: "Inter, Helvetica, Arial, sans-serif", color: "#ffffffaa", fontSize: 26 }}>
      <div style={{ height: 6, borderRadius: 3, background: "#ffffff22", overflow: "hidden" }}>
        <div style={{ width: `${p * 100}%`, height: "100%", background: `linear-gradient(90deg, ${ACCENT_B}, ${ACCENT_A})` }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 10 }}>
        <span>{fmt(frame / 30)}</span>
        <span>{fmt(CLIP_SECONDS)}</span>
      </div>
    </div>
  );
};

const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [DURATION - 40, DURATION - 5], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.ease),
  });
  if (o === 0) return null;
  return (
    <AbsoluteFill style={{ background: `rgba(5,5,10,${o * 0.92})`, justifyContent: "center", alignItems: "center" }}>
      <div style={{ fontFamily: "Inter, Helvetica, Arial, sans-serif", fontSize: 90, fontWeight: 900, color: "white", opacity: o, transform: `scale(${0.9 + 0.1 * o})`, textAlign: "center" }}>
        keep it
        <div style={{ background: `linear-gradient(90deg, ${ACCENT_A}, ${ACCENT_C})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>on repeat</div>
      </div>
    </AbsoluteFill>
  );
};

export const SavedSounds: React.FC = () => {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: fadeIn }}>
      <Background />
      <Title />
      <Card />
      <NowPlaying />
      <Visualizer />
      <Progress />
      <Outro />
    </AbsoluteFill>
  );
};
