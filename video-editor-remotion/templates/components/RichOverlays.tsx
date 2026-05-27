import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

// New Remotion-package-backed overlays added in the skill upgrade.
// See references/remotion-feature-catalog.md for the full inventory.
import { TransitionScene } from "./TransitionScene";
import { AudioWaveform } from "./AudioWaveform";
import { LottieScene } from "./LottieScene";
import { RiveScene } from "./RiveScene";
import { ThreeReveal } from "./ThreeReveal";
import { MotionBlurOverlay } from "./MotionBlurOverlay";
import { NoiseBackground } from "./NoiseBackground";
import { ShapeMorph } from "./ShapeMorph";

const COPPER = "#B87333";
const COPPER_DARK = "#8B3A1F";
const BEIGE = "#F5F1E8";
const GREEN_DARK = "#0A1A0F";
const GREEN_PRIMARY = "#1F4D2C";

const cubicOut = Easing.bezier(0.16, 1, 0.3, 1);

type BaseProps = { startFrame: number; endFrame: number };

const useRel = (startFrame: number, endFrame: number) => {
  const frame = useCurrentFrame();
  const local = frame - startFrame;
  const dur = endFrame - startFrame;
  return { frame, local, dur, t: Math.max(0, Math.min(1, local / dur)) };
};

// ──────────────────────────────────────────────────────────────────
// 1. StampBrand — circular rotating stamp (ART. 118 CTN)
// ──────────────────────────────────────────────────────────────────
export const StampBrand: React.FC<BaseProps & { text: string; position?: string }> = ({
  startFrame, endFrame, text, position = "top-right",
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 14 } });
  const exit = local > dur - fps ? interpolate(local, [dur - fps, dur], [1, 0]) : 1;
  const rotate = local * 0.5;
  const opacity = entry * exit;

  const pos: React.CSSProperties =
    position === "top-right" ? { top: 80, right: 60 } :
    position === "top-left" ? { top: 80, left: 60 } :
    { top: 80, right: 60 };

  const radius = 90;
  const stamp = (
    <div style={{
      position: "absolute", ...pos, width: radius * 2, height: radius * 2,
      transform: `rotate(${rotate}deg) scale(${entry})`, opacity,
    }}>
      <svg viewBox="-100 -100 200 200" width={radius * 2} height={radius * 2}>
        <defs>
          <path id="stamp-circle" d="M 0,0 m -75,0 a 75,75 0 1,1 150,0 a 75,75 0 1,1 -150,0" />
        </defs>
        <circle r="90" fill="none" stroke={COPPER} strokeWidth="4" />
        <circle r="80" fill="none" stroke={COPPER} strokeWidth="2" />
        <text fill={COPPER} fontSize="14" fontWeight="900" letterSpacing="3" textAnchor="middle">
          <textPath href="#stamp-circle" startOffset="25%">VIGENTE • LEGAL</textPath>
        </text>
        <text fill={COPPER} fontSize="22" fontWeight="900" textAnchor="middle" y="8">{text}</text>
      </svg>
    </div>
  );
  return stamp;
};

// ──────────────────────────────────────────────────────────────────
// 2. RomanScrollWipe — pergaminho desenrolando
// ──────────────────────────────────────────────────────────────────
export const RomanScrollWipe: React.FC<BaseProps & { direction?: "left" | "right" }> = ({
  startFrame, endFrame, direction = "right",
}) => {
  const { local, dur } = useRel(startFrame, endFrame);
  const t = interpolate(local, [0, dur], [0, 1], { extrapolateRight: "clamp", easing: cubicOut });
  const w = 1080 * t;
  const fromLeft = direction === "right";

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width="1080" height="1920" viewBox="0 0 1080 1920">
        <defs>
          <pattern id="papyrus" patternUnits="userSpaceOnUse" width="200" height="200">
            <rect width="200" height="200" fill="#E8DDC0" />
            <circle cx="50" cy="80" r="1" fill="#8B7355" opacity="0.3" />
            <circle cx="150" cy="120" r="0.8" fill="#8B7355" opacity="0.2" />
            <circle cx="100" cy="50" r="1.2" fill="#8B7355" opacity="0.25" />
          </pattern>
        </defs>
        <rect
          x={fromLeft ? 0 : 1080 - w}
          y="0" width={w} height="1920"
          fill="url(#papyrus)"
        />
        {/* roller edge */}
        <ellipse
          cx={fromLeft ? w : 1080 - w} cy="960"
          rx="20" ry="960" fill={COPPER_DARK}
        />
      </svg>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 3. RomanColumnsBg — coliseum silhouette behind talking head
// ──────────────────────────────────────────────────────────────────
export const RomanColumnsBg: React.FC<BaseProps & { opacity?: number }> = ({
  startFrame, endFrame, opacity = 0.18,
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const fadeIn = interpolate(local, [0, fps * 0.8], [0, opacity], { extrapolateRight: "clamp" });
  const fadeOut = local > dur - fps * 0.5 ? interpolate(local, [dur - fps * 0.5, dur], [opacity, 0]) : opacity;
  const op = Math.min(fadeIn, fadeOut);

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
      <svg width="1080" height="1920" viewBox="0 0 1080 1920">
        {/* sun radial gradient */}
        <defs>
          <radialGradient id="sun-glow" cx="50%" cy="35%">
            <stop offset="0%" stopColor={COPPER} stopOpacity="0.6" />
            <stop offset="100%" stopColor={COPPER} stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="540" cy="700" r="500" fill="url(#sun-glow)" />
        {/* coliseum arcades silhouette — bottom 1/3 */}
        <g fill={COPPER} opacity="0.7">
          {[...Array(12)].map((_, i) => (
            <g key={i} transform={`translate(${50 + i * 85}, 1450)`}>
              <rect x="0" y="0" width="60" height="200" rx="0" />
              <path d="M 5,0 Q 30,-40 55,0 L 55,40 L 5,40 Z" fill={GREEN_DARK} />
            </g>
          ))}
          <rect x="0" y="1640" width="1080" height="20" />
          <rect x="0" y="1700" width="1080" height="220" opacity="0.4" />
        </g>
      </svg>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 4. YearCaption — "ROMA — 70 d.C." serif label
// ──────────────────────────────────────────────────────────────────
export const YearCaption: React.FC<BaseProps & { text: string; position?: string }> = ({
  startFrame, endFrame, text, position = "bottom-left",
}) => {
  const { fps } = useVideoConfig();
  const { local } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 18 } });
  const slide = interpolate(entry, [0, 1], [40, 0]);

  const style: React.CSSProperties =
    position === "bottom-left" ? { bottom: 380, left: 60 } :
    position === "bottom-right" ? { bottom: 380, right: 60 } :
    { top: 200, left: 60 };

  return (
    <div style={{
      position: "absolute", ...style,
      transform: `translateY(${slide}px)`, opacity: entry,
      fontFamily: "Georgia, 'Playfair Display', serif",
      fontSize: 56, color: BEIGE, letterSpacing: "0.15em",
      textShadow: `2px 2px 8px ${GREEN_DARK}`,
      borderLeft: `4px solid ${COPPER}`, paddingLeft: 18,
    }}>
      {text}
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// 5. VespasianBust — Roman emperor profile (coin-style)
// ──────────────────────────────────────────────────────────────────
export const VespasianBust: React.FC<BaseProps & { position?: string }> = ({
  startFrame, endFrame, position = "right",
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 16 } });
  const wobble = Math.sin(local / 30) * 3;
  const exit = local > dur - fps * 0.5 ? interpolate(local, [dur - fps * 0.5, dur], [1, 0]) : 1;

  const pos: React.CSSProperties =
    position === "right" ? { right: 60, top: 180 } :
    position === "left" ? { left: 60, top: 180 } :
    { right: 60, top: 180 };

  return (
    <div style={{
      position: "absolute", ...pos,
      transform: `translateY(${interpolate(entry, [0, 1], [80, 0])}px) rotate(${wobble * 0.3}deg) scale(${entry})`,
      opacity: entry * exit,
    }}>
      <svg width="280" height="320" viewBox="-140 -160 280 320">
        <defs>
          <radialGradient id="coin-bg" cx="50%" cy="50%">
            <stop offset="0%" stopColor="#D4A857" />
            <stop offset="100%" stopColor={COPPER_DARK} />
          </radialGradient>
        </defs>
        <circle r="130" fill="url(#coin-bg)" stroke={COPPER} strokeWidth="6" />
        <circle r="120" fill="none" stroke={COPPER_DARK} strokeWidth="2" strokeDasharray="3 3" />
        {/* Profile silhouette — stylized Roman bust */}
        <g fill={GREEN_DARK} stroke={GREEN_DARK} strokeWidth="2">
          <path d="M -40,-80 Q -60,-90 -50,-50 Q -70,-30 -55,0 Q -65,15 -55,30 Q -50,50 -30,55 L -40,80 L 50,80 L 40,30 Q 30,20 35,5 Q 45,-10 35,-30 Q 50,-55 30,-75 Q 25,-85 5,-90 Q -20,-92 -40,-80 Z" />
          {/* laurel wreath */}
          <ellipse cx="0" cy="-95" rx="55" ry="12" fill="none" stroke={COPPER} strokeWidth="3" />
          {[...Array(7)].map((_, i) => {
            const a = -Math.PI + (Math.PI * (i + 1)) / 8;
            const x = Math.cos(a) * 55;
            const y = Math.sin(a) * 12 - 95;
            return <ellipse key={i} cx={x} cy={y} rx="8" ry="3" fill={COPPER} transform={`rotate(${(a * 180) / Math.PI + 90} ${x} ${y})`} />;
          })}
        </g>
        <text y="115" textAnchor="middle" fill={COPPER_DARK} fontSize="14" fontWeight="900" letterSpacing="3">VESPASIANVS</text>
      </svg>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// 6. RomanLatrine — ancient stone bench with holes
// ──────────────────────────────────────────────────────────────────
export const RomanLatrine: React.FC<BaseProps> = ({ startFrame, endFrame }) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 14 } });
  const exit = local > dur - fps * 0.4 ? interpolate(local, [dur - fps * 0.4, dur], [1, 0]) : 1;

  return (
    <div style={{
      position: "absolute", left: 60, bottom: 480,
      transform: `translateY(${interpolate(entry, [0, 1], [60, 0])}px) scale(${entry})`,
      opacity: entry * exit,
    }}>
      <svg width="320" height="180" viewBox="0 0 320 180">
        {/* stone bench */}
        <rect x="10" y="40" width="300" height="100" fill="#8B7355" stroke={COPPER} strokeWidth="3" rx="8" />
        <rect x="10" y="130" width="300" height="20" fill={COPPER_DARK} rx="4" />
        {/* three dark holes */}
        {[60, 160, 260].map((cx) => (
          <ellipse key={cx} cx={cx} cy="65" rx="35" ry="18" fill={GREEN_DARK} stroke={COPPER_DARK} strokeWidth="2" />
        ))}
        {/* texture lines */}
        <line x1="20" y1="100" x2="300" y2="100" stroke={COPPER_DARK} strokeWidth="1" opacity="0.4" />
        <text x="160" y="175" textAnchor="middle" fill={BEIGE} fontSize="14" fontWeight="900" letterSpacing="2">LATRINA PVBLICA</text>
      </svg>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// 7. GoldCoinDrop — coin falling, spinning, landing with flash
// ──────────────────────────────────────────────────────────────────
export const GoldCoinDrop: React.FC<BaseProps & { land_at?: number }> = ({
  startFrame, endFrame, land_at,
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  // land_at is the local frame at which the coin lands (already converted by renderer).
  // Default: 55% of duration if not specified.
  const landFrame = land_at !== undefined ? land_at : Math.round(dur * 0.55);
  const fall = interpolate(local, [0, landFrame], [-700, 0], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.55, 0, 0.95, 0.5),
  });
  const rot = interpolate(local, [0, landFrame], [0, 720], { extrapolateRight: "clamp" });
  const bounce = local > landFrame ? interpolate(local, [landFrame, landFrame + 8, landFrame + 16], [0, -30, 0], {
    extrapolateRight: "clamp",
  }) : 0;
  const flash = local > landFrame ? interpolate(local, [landFrame, landFrame + 6], [1, 0], { extrapolateRight: "clamp" }) : 0;
  const exit = local > dur - fps * 0.3 ? interpolate(local, [dur - fps * 0.3, dur], [1, 0]) : 1;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* radial flash on land */}
      {flash > 0 && (
        <div style={{
          position: "absolute", left: "50%", top: "55%",
          width: 600, height: 600, marginLeft: -300, marginTop: -300,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${COPPER}cc 0%, transparent 60%)`,
          opacity: flash,
        }} />
      )}
      <div style={{
        position: "absolute", left: "50%", top: "55%",
        transform: `translate(-50%, ${fall + bounce}px) rotateY(${rot}deg)`,
        opacity: exit,
      }}>
        <svg width="180" height="180" viewBox="-90 -90 180 180">
          <defs>
            <radialGradient id="coin-grad" cx="35%" cy="35%">
              <stop offset="0%" stopColor="#FFE188" />
              <stop offset="60%" stopColor={COPPER} />
              <stop offset="100%" stopColor={COPPER_DARK} />
            </radialGradient>
          </defs>
          <circle r="80" fill="url(#coin-grad)" stroke={COPPER_DARK} strokeWidth="4" />
          <circle r="68" fill="none" stroke={COPPER_DARK} strokeWidth="2" />
          <text textAnchor="middle" y="-15" fill={COPPER_DARK} fontSize="14" fontWeight="900" letterSpacing="2">SPQR</text>
          <text textAnchor="middle" y="15" fill={COPPER_DARK} fontSize="32" fontWeight="900">$</text>
          <text textAnchor="middle" y="40" fill={COPPER_DARK} fontSize="11" fontWeight="900" letterSpacing="1">VESP</text>
        </svg>
      </div>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 8. CinematicTitle — big serif title (PECUNIA NON OLET)
// ──────────────────────────────────────────────────────────────────
export const CinematicTitle: React.FC<BaseProps & {
  text: string; subtitle?: string; font_family?: string; position?: string;
}> = ({ startFrame, endFrame, text, subtitle, font_family = "serif", position = "center" }) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const letters = text.split("");
  const exit = local > dur - fps * 0.6 ? interpolate(local, [dur - fps * 0.6, dur], [1, 0]) : 1;
  const subEntry = spring({ frame: local - fps * 0.8, fps, config: { damping: 18 } });
  const lineDraw = interpolate(local, [fps * 0.4, fps * 1.2], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{
      pointerEvents: "none",
      background: `linear-gradient(180deg, ${GREEN_DARK}f0 0%, ${GREEN_DARK}d0 100%)`,
      opacity: exit,
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
    }}>
      <div style={{
        fontFamily: `Georgia, 'Playfair Display', 'Cinzel', ${font_family}`,
        fontSize: 110, fontWeight: 900, color: COPPER,
        letterSpacing: "0.04em", textAlign: "center",
        textShadow: `4px 4px 20px ${GREEN_DARK}`,
        lineHeight: 1.1,
      }}>
        {letters.map((char, i) => {
          const charEntry = spring({
            frame: local - i * 2, fps, config: { damping: 16 },
          });
          return (
            <span key={i} style={{
              display: "inline-block",
              opacity: charEntry,
              transform: `translateY(${interpolate(charEntry, [0, 1], [40, 0])}px)`,
            }}>{char === " " ? " " : char}</span>
          );
        })}
      </div>
      {/* underline */}
      <div style={{
        height: 4, width: 600 * lineDraw, background: COPPER,
        marginTop: 24, transition: "width 0.3s",
      }} />
      {subtitle && (
        <div style={{
          marginTop: 28, opacity: subEntry,
          transform: `translateY(${interpolate(subEntry, [0, 1], [20, 0])}px)`,
          fontFamily: "Georgia, serif", fontStyle: "italic",
          fontSize: 42, color: BEIGE, letterSpacing: "0.05em",
          textAlign: "center", maxWidth: 900,
        }}>
          {subtitle}
        </div>
      )}
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 9. CodeDocument — open law code overlay (semi-transparent)
// ──────────────────────────────────────────────────────────────────
export const CodeDocument: React.FC<BaseProps & { article: string; title?: string }> = ({
  startFrame, endFrame, article, title = "CÓDIGO TRIBUTÁRIO NACIONAL",
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 16 } });
  const exit = local > dur - fps * 0.6 ? interpolate(local, [dur - fps * 0.6, dur], [1, 0]) : 1;

  return (
    <div style={{
      position: "absolute", top: 220, left: 60, right: 60,
      transform: `translateY(${interpolate(entry, [0, 1], [60, 0])}px)`,
      opacity: entry * exit * 0.92,
    }}>
      <div style={{
        background: BEIGE, borderRadius: 12, padding: "32px 40px",
        boxShadow: `0 20px 60px ${GREEN_DARK}`,
        border: `3px solid ${COPPER}`,
      }}>
        <div style={{
          fontSize: 22, fontWeight: 900, color: COPPER_DARK, letterSpacing: 4,
          paddingBottom: 12, borderBottom: `2px solid ${COPPER_DARK}`,
        }}>{title}</div>
        <div style={{
          marginTop: 24, fontSize: 88, fontWeight: 900, color: COPPER_DARK,
          fontFamily: "Georgia, serif", letterSpacing: "0.02em",
        }}>
          ART. {article}
        </div>
        <div style={{
          marginTop: 8, fontSize: 32, color: GREEN_DARK, fontStyle: "italic",
          fontFamily: "Georgia, serif", lineHeight: 1.4,
        }}>
          "A definição legal do fato gerador é interpretada de forma <span style={{ background: `${COPPER}55`, padding: "2px 6px", borderRadius: 4 }}>objetiva</span>..."
        </div>
      </div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// 10. SplitComparison — two icons facing each other
// ──────────────────────────────────────────────────────────────────
const PadariaIcon = ({ size = 180 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={BEIGE} strokeWidth="1.5">
    <path d="M3 21V8l9-5 9 5v13M3 21h18M9 21v-6h6v6" />
    <path d="M5 12h14M7 8h10" />
  </svg>
);
const ShadowIcon = ({ size = 180 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={COPPER_DARK} strokeWidth="1.5">
    <path d="M12 4a4 4 0 0 1 4 4v0a4 4 0 0 1-8 0v0a4 4 0 0 1 4-4z" />
    <path d="M5 21v-2a4 4 0 0 1 4-4h6a4 4 0 0 1 4 4v2" />
    <path d="M2 14l4-2M22 14l-4-2" strokeDasharray="2 2" />
  </svg>
);

export const SplitComparison: React.FC<BaseProps & {
  left_icon: string; right_icon: string; left_label: string; right_label: string;
}> = ({ startFrame, endFrame, left_icon, right_icon, left_label, right_label }) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 16 } });
  const pulse = 1 + Math.sin(local / 8) * 0.05;
  const exit = local > dur - fps * 0.5 ? interpolate(local, [dur - fps * 0.5, dur], [1, 0]) : 1;

  const Card = ({ icon, label, side }: { icon: React.ReactNode; label: string; side: "left" | "right" }) => (
    <div style={{
      position: "absolute", top: 700, [side]: 60,
      width: 380, padding: 32,
      background: side === "left" ? `${BEIGE}15` : `${COPPER_DARK}30`,
      border: `3px solid ${side === "left" ? BEIGE : COPPER_DARK}`,
      borderRadius: 16,
      transform: `translateX(${side === "left" ? interpolate(entry, [0, 1], [-100, 0]) : interpolate(entry, [0, 1], [100, 0])}px) scale(${pulse})`,
      opacity: entry * exit,
      display: "flex", flexDirection: "column", alignItems: "center", gap: 24,
    }}>
      {icon}
      <div style={{
        fontSize: 36, fontWeight: 900, color: side === "left" ? BEIGE : COPPER,
        letterSpacing: 2, textAlign: "center",
      }}>{label}</div>
    </div>
  );

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <Card icon={left_icon === "padaria" ? <PadariaIcon /> : <ShadowIcon />} label={left_label} side="left" />
      <Card icon={right_icon === "shadow" ? <ShadowIcon /> : <PadariaIcon />} label={right_label} side="right" />
      {/* VS divider */}
      <div style={{
        position: "absolute", top: 850, left: "50%", transform: "translateX(-50%)",
        fontSize: 64, fontWeight: 900, color: COPPER, opacity: entry * exit,
        textShadow: `0 4px 12px ${GREEN_DARK}`,
      }}>↔</div>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 11. MergeIntoKeyword — central keyword reveal
// ──────────────────────────────────────────────────────────────────
export const MergeIntoKeyword: React.FC<BaseProps & { text: string }> = ({
  startFrame, endFrame, text,
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 12, stiffness: 180 } });
  const exit = local > dur - fps * 0.4 ? interpolate(local, [dur - fps * 0.4, dur], [1, 0]) : 1;

  return (
    <div style={{
      position: "absolute", top: 700, left: 0, right: 0,
      textAlign: "center", opacity: entry * exit,
    }}>
      <div style={{
        display: "inline-block",
        background: COPPER, color: GREEN_DARK,
        padding: "24px 48px", borderRadius: 8,
        fontSize: 64, fontWeight: 900, letterSpacing: 3,
        transform: `scale(${entry})`,
        boxShadow: `0 12px 40px ${GREEN_DARK}, 0 0 60px ${COPPER}66`,
      }}>{text}</div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// 12. STFStamp — Brazilian Supreme Court stamp impact
// ──────────────────────────────────────────────────────────────────
export const STFStamp: React.FC<BaseProps & { text: string }> = ({
  startFrame, endFrame, text,
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 8, stiffness: 220 } });
  const scale = interpolate(entry, [0, 1], [2.0, 1.0]);
  const tilt = interpolate(entry, [0, 1], [-12, -6]);
  // shake on impact
  const shake = local < 5 ? Math.sin(local * 4) * 6 : 0;
  const exit = local > dur - fps * 0.5 ? interpolate(local, [dur - fps * 0.5, dur], [1, 0]) : 1;

  return (
    <div style={{
      position: "absolute", top: 280, right: 80,
      transform: `translate(${shake}px, ${shake}px) rotate(${tilt}deg) scale(${scale})`,
      opacity: entry * exit,
    }}>
      <svg width="320" height="320" viewBox="-160 -160 320 320">
        <defs>
          <path id="stf-circle" d="M 0,0 m -120,0 a 120,120 0 1,1 240,0 a 120,120 0 1,1 -240,0" />
        </defs>
        <circle r="140" fill="none" stroke={COPPER_DARK} strokeWidth="6" />
        <circle r="125" fill={COPPER_DARK} opacity="0.12" />
        <circle r="115" fill="none" stroke={COPPER_DARK} strokeWidth="3" />
        {/* stars in arc */}
        {[...Array(11)].map((_, i) => {
          const a = -Math.PI * 1.1 + (Math.PI * 1.2 * i) / 10;
          const x = Math.cos(a) * 95;
          const y = Math.sin(a) * 95;
          return <text key={i} x={x} y={y + 5} textAnchor="middle" fill={COPPER_DARK} fontSize="14">★</text>;
        })}
        {/* scale of justice icon */}
        <g fill="none" stroke={COPPER_DARK} strokeWidth="3">
          <line x1="0" y1="-50" x2="0" y2="30" />
          <line x1="-40" y1="-30" x2="40" y2="-30" />
          <circle cx="-40" cy="-30" r="14" fill={COPPER_DARK}/>
          <circle cx="40" cy="-30" r="14" fill={COPPER_DARK}/>
          <rect x="-15" y="30" width="30" height="8" fill={COPPER_DARK} />
        </g>
        <text textAnchor="middle" y="60" fill={COPPER_DARK} fontSize="16" fontWeight="900" letterSpacing="2">{text}</text>
        <text fill={COPPER_DARK} fontSize="11" fontWeight="900" letterSpacing="3">
          <textPath href="#stf-circle" startOffset="25%">SUPREMO TRIBUNAL FEDERAL</textPath>
        </text>
      </svg>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// 13. TickerResp — vertical scrolling REsps
// ──────────────────────────────────────────────────────────────────
export const TickerResp: React.FC<BaseProps & { items: string[] }> = ({
  startFrame, endFrame, items,
}) => {
  const { local, dur } = useRel(startFrame, endFrame);
  const scrollY = interpolate(local, [0, dur], [0, -items.length * 60]);
  return (
    <div style={{
      position: "absolute", left: 60, top: 1300, width: 360,
      opacity: 0.55, fontFamily: "Menlo, 'JetBrains Mono', monospace",
      fontSize: 22, color: BEIGE,
      transform: `translateY(${scrollY}px)`,
      overflow: "hidden", height: 200,
    }}>
      {items.concat(items).map((item, i) => (
        <div key={i} style={{ height: 60, lineHeight: "60px", letterSpacing: 1 }}>{item}</div>
      ))}
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// 14. ScaleOfJustice — balance scale tilting
// ──────────────────────────────────────────────────────────────────
export const ScaleOfJustice: React.FC<BaseProps & {
  left_weight?: number; right_weight?: number;
}> = ({ startFrame, endFrame, left_weight = 1, right_weight = 1 }) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 14 } });
  // Tilt: positive = left down (left heavier), negative = right down
  const targetTilt = (left_weight - right_weight) * 8;
  const tilt = interpolate(entry, [0, 1], [0, targetTilt]) + Math.sin(local / 20) * 0.6;
  const exit = local > dur - fps * 0.5 ? interpolate(local, [dur - fps * 0.5, dur], [1, 0]) : 1;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: entry * exit }}>
      <svg width="1080" height="1920" viewBox="0 0 1080 1920">
        {/* central pillar */}
        <g transform="translate(540, 900)">
          <rect x="-8" y="-180" width="16" height="380" fill={COPPER} />
          {/* base */}
          <rect x="-90" y="200" width="180" height="20" fill={COPPER_DARK} rx="4" />
          <rect x="-110" y="220" width="220" height="10" fill={COPPER_DARK} rx="4" />
          {/* beam */}
          <g transform={`rotate(${tilt})`}>
            <rect x="-250" y="-185" width="500" height="14" fill={COPPER} rx="4" />
            {/* left plate (heavier — going down) */}
            <g transform={`translate(-220, ${-178 + Math.max(0, tilt) * 4})`}>
              <line x1="0" y1="0" x2="0" y2="40" stroke={COPPER} strokeWidth="3" />
              <ellipse cx="0" cy="48" rx="80" ry="14" fill={COPPER} />
              <text textAnchor="middle" y="78" fill={BEIGE} fontSize="20" fontWeight="900" letterSpacing="2">EMPRESÁRIO</text>
              <text textAnchor="middle" y="100" fill={BEIGE} fontSize="20" fontWeight="900" letterSpacing="2">HONESTO</text>
            </g>
            {/* right plate (lighter — staying up) */}
            <g transform={`translate(220, ${-178 - Math.max(0, -tilt) * 4})`}>
              <line x1="0" y1="0" x2="0" y2="40" stroke={COPPER} strokeWidth="3" />
              <ellipse cx="0" cy="48" rx="80" ry="14" fill={COPPER_DARK} />
              <text textAnchor="middle" y="78" fill={BEIGE} fontSize="20" fontWeight="900" letterSpacing="2">CRIMINOSO</text>
              <text textAnchor="middle" y="100" fill={BEIGE} fontSize="20" fontWeight="900" letterSpacing="2">"INVISÍVEL"</text>
            </g>
          </g>
        </g>
      </svg>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 15. ContextTags — floating pill tags around 37%
// ──────────────────────────────────────────────────────────────────
export const ContextTags: React.FC<BaseProps & { tags: string[] }> = ({
  startFrame, endFrame, tags,
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const exit = local > dur - fps * 0.4 ? interpolate(local, [dur - fps * 0.4, dur], [1, 0]) : 1;

  // Position tags in a circle around center
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {tags.map((tag, i) => {
        const tagEntry = spring({ frame: local - i * 4, fps, config: { damping: 16 } });
        const angle = (i / tags.length) * Math.PI * 2 - Math.PI / 2;
        const radius = 380;
        const x = 540 + Math.cos(angle) * radius;
        const y = 1100 + Math.sin(angle) * radius * 0.5;
        return (
          <div key={i} style={{
            position: "absolute", left: x, top: y, transform: `translate(-50%, -50%) scale(${tagEntry})`,
            opacity: tagEntry * exit,
            background: "transparent", color: COPPER, border: `2px solid ${COPPER}`,
            padding: "8px 18px", borderRadius: 99,
            fontSize: 24, fontWeight: 900, letterSpacing: 2,
          }}>{tag}</div>
        );
      })}
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 16. CounterNumber — animated counting number
// ──────────────────────────────────────────────────────────────────
export const CounterNumber: React.FC<BaseProps & {
  from?: number; to: number; suffix?: string; subtitle?: string;
}> = ({ startFrame, endFrame, from = 0, to, suffix = "", subtitle }) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const countDur = Math.min(fps * 1.4, dur * 0.6);
  const value = Math.round(interpolate(local, [0, countDur], [from, to], {
    extrapolateRight: "clamp", easing: cubicOut,
  }));
  const entry = spring({ frame: local, fps, config: { damping: 14 } });
  const finalPulse = local > countDur ? 1 + Math.sin((local - countDur) / 6) * 0.04 : 1;
  const exit = local > dur - fps * 0.5 ? interpolate(local, [dur - fps * 0.5, dur], [1, 0]) : 1;

  return (
    <AbsoluteFill style={{
      pointerEvents: "none", display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", opacity: entry * exit,
    }}>
      <div style={{
        fontSize: 320, fontWeight: 900, color: COPPER,
        letterSpacing: "-0.03em",
        transform: `scale(${entry * finalPulse})`,
        textShadow: `0 12px 40px ${GREEN_DARK}, 0 0 80px ${COPPER}66`,
        lineHeight: 1,
      }}>{value}{suffix}</div>
      {subtitle && (
        <div style={{
          marginTop: 24, fontSize: 36, color: BEIGE, fontStyle: "italic",
          letterSpacing: 2, textAlign: "center", maxWidth: 800,
        }}>{subtitle}</div>
      )}
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 17. DataNetwork — connected dots animation
// ──────────────────────────────────────────────────────────────────
export const DataNetwork: React.FC<BaseProps & { node_count?: number }> = ({
  startFrame, endFrame, node_count = 60,
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const exit = local > dur - fps * 0.5 ? interpolate(local, [dur - fps * 0.5, dur], [1, 0]) : 1;

  // Pseudo-random but deterministic node positions
  const nodes = React.useMemo(() => {
    return Array.from({ length: node_count }, (_, i) => {
      const seed = i * 9301 + 49297;
      const x = ((seed * 1103515245 + 12345) % 1080) / 1;
      const y = ((seed * 1664525 + 1013904223) % 1920) / 1;
      return { x, y };
    });
  }, [node_count]);

  // Connections between nearby nodes
  const connections = React.useMemo(() => {
    const conns: [number, number][] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        if (Math.sqrt(dx * dx + dy * dy) < 220) conns.push([i, j]);
      }
    }
    return conns.slice(0, 80);
  }, [nodes]);

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: 0.4 * exit }}>
      <svg width="1080" height="1920" viewBox="0 0 1080 1920">
        {connections.map(([a, b], i) => {
          const appear = interpolate(local, [i * 0.3, i * 0.3 + 6], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          return (
            <line key={i}
              x1={nodes[a].x} y1={nodes[a].y}
              x2={nodes[b].x} y2={nodes[b].y}
              stroke={COPPER} strokeWidth="1" opacity={appear * 0.5}
            />
          );
        })}
        {nodes.map((n, i) => {
          const pulse = 1 + Math.sin((local + i * 4) / 12) * 0.4;
          const appear = interpolate(local, [i * 0.2, i * 0.2 + 4], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          return (
            <circle key={i} cx={n.x} cy={n.y} r={2 * pulse}
              fill={COPPER} opacity={appear} />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 18. MismatchCards — declared vs actual patrimônio
// ──────────────────────────────────────────────────────────────────
export const MismatchCards: React.FC<BaseProps & {
  declared_label: string; declared_value: string;
  actual_label: string; actual_value: string;
}> = ({ startFrame, endFrame, declared_label, declared_value, actual_label, actual_value }) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entryL = spring({ frame: local, fps, config: { damping: 16 } });
  const entryR = spring({ frame: local - 8, fps, config: { damping: 16 } });
  const arrow = interpolate(local, [fps * 1.2, fps * 1.8], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const exit = local > dur - fps * 0.5 ? interpolate(local, [dur - fps * 0.5, dur], [1, 0]) : 1;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Declared (small, beige) */}
      <div style={{
        position: "absolute", top: 600, left: 80, width: 380,
        background: `${BEIGE}1A`, border: `2px solid ${BEIGE}`, borderRadius: 12,
        padding: "24px 28px",
        transform: `translateX(${interpolate(entryL, [0, 1], [-80, 0])}px) scale(${0.85 + entryL * 0.15})`,
        opacity: entryL * exit,
      }}>
        <div style={{ fontSize: 22, color: BEIGE, letterSpacing: 3, fontWeight: 900 }}>{declared_label}</div>
        <div style={{ marginTop: 8, fontSize: 56, color: BEIGE, fontWeight: 900, letterSpacing: -1 }}>{declared_value}</div>
      </div>
      {/* Actual (large, copper) */}
      <div style={{
        position: "absolute", top: 880, right: 60, width: 580,
        background: `${COPPER}25`, border: `4px solid ${COPPER}`, borderRadius: 16,
        padding: "32px 36px",
        transform: `translateX(${interpolate(entryR, [0, 1], [120, 0])}px) scale(${0.85 + entryR * 0.15})`,
        opacity: entryR * exit,
        boxShadow: `0 16px 50px ${COPPER}44`,
      }}>
        <div style={{ fontSize: 28, color: COPPER, letterSpacing: 4, fontWeight: 900 }}>{actual_label}</div>
        <div style={{ marginTop: 12, fontSize: 96, color: COPPER, fontWeight: 900, letterSpacing: -2 }}>{actual_value}</div>
      </div>
      {/* Arrow */}
      <svg width="1080" height="1920" viewBox="0 0 1080 1920" style={{ position: "absolute", inset: 0, opacity: arrow * exit }}>
        <path d="M 250 700 Q 540 800 700 880" stroke={COPPER} strokeWidth="6" fill="none" strokeDasharray="10 8" />
        <polygon points="690,860 720,890 690,900" fill={COPPER} />
        <text x="540" y="780" textAnchor="middle" fill={COPPER} fontSize="32" fontWeight="900" letterSpacing="3">INCOMPATÍVEL</text>
      </svg>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 19. TributavelStamp — quick "TRIBUTÁVEL" stamp
// ──────────────────────────────────────────────────────────────────
export const TributavelStamp: React.FC<BaseProps & { text: string }> = ({
  startFrame, endFrame, text,
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 6, stiffness: 250 } });
  const scale = interpolate(entry, [0, 1], [3, 1]);
  const exit = local > dur - fps * 0.4 ? interpolate(local, [dur - fps * 0.4, dur], [1, 0]) : 1;

  return (
    <div style={{
      position: "absolute", top: 1200, left: "50%",
      transform: `translateX(-50%) rotate(-8deg) scale(${scale})`,
      opacity: entry * exit,
    }}>
      <div style={{
        border: `6px solid ${COPPER_DARK}`,
        padding: "12px 32px",
        fontSize: 56, fontWeight: 900, color: COPPER_DARK,
        letterSpacing: 6,
        background: `${BEIGE}DD`, borderRadius: 4,
      }}>
        {text}
      </div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// 20. WarmShiftPivot — color shift overlay (problem→solution)
// ──────────────────────────────────────────────────────────────────
export const WarmShiftPivot: React.FC<BaseProps> = ({ startFrame, endFrame }) => {
  const { local, dur } = useRel(startFrame, endFrame);
  const opacity = interpolate(local, [0, dur * 0.5, dur], [0, 0.5, 0]);
  return (
    <AbsoluteFill style={{
      pointerEvents: "none",
      background: `radial-gradient(circle at 50% 50%, ${COPPER}80 0%, ${COPPER}00 70%)`,
      opacity,
    }} />
  );
};

// ──────────────────────────────────────────────────────────────────
// 21. TriboShield — protective shield with orbiting docs
// ──────────────────────────────────────────────────────────────────
export const TriboShield: React.FC<BaseProps & { show_orbit?: boolean }> = ({
  startFrame, endFrame, show_orbit = true,
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 14 } });
  const stroke = interpolate(local, [0, fps * 1.2], [0, 1], { extrapolateRight: "clamp" });
  const fill = interpolate(local, [fps * 1.2, fps * 1.8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const checkScale = spring({ frame: local - fps * 1.6, fps, config: { damping: 12 } });
  const orbit = local * 1.5;
  const exit = local > dur - fps * 0.6 ? interpolate(local, [dur - fps * 0.6, dur], [1, 0]) : 1;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: exit }}>
      <div style={{
        position: "absolute", top: 380, left: "50%", transform: `translateX(-50%) scale(${entry})`,
      }}>
        <svg width="500" height="500" viewBox="-250 -250 500 500">
          {/* Orbit docs */}
          {show_orbit && [0, 90, 180, 270].map((a, i) => {
            const ang = ((orbit + a) * Math.PI) / 180;
            const x = Math.cos(ang) * 220;
            const y = Math.sin(ang) * 220;
            return (
              <g key={i} transform={`translate(${x}, ${y})`} opacity={entry}>
                <rect x="-20" y="-26" width="40" height="52" rx="4" fill={BEIGE} stroke={COPPER} strokeWidth="2" />
                <line x1="-12" y1="-12" x2="12" y2="-12" stroke={COPPER_DARK} strokeWidth="2" />
                <line x1="-12" y1="-2" x2="12" y2="-2" stroke={COPPER_DARK} strokeWidth="2" />
                <line x1="-12" y1="8" x2="6" y2="8" stroke={COPPER_DARK} strokeWidth="2" />
              </g>
            );
          })}
          {/* shield */}
          <path
            d="M 0,-180 L 130,-130 L 130,30 Q 130,140 0,200 Q -130,140 -130,30 L -130,-130 Z"
            fill={COPPER} fillOpacity={fill}
            stroke={COPPER} strokeWidth="6"
            strokeDasharray="800"
            strokeDashoffset={(1 - stroke) * 800}
          />
          {/* check */}
          <path d="M -50,0 L -10,40 L 60,-40"
            fill="none" stroke={GREEN_DARK} strokeWidth="14"
            strokeLinecap="round" strokeLinejoin="round"
            transform={`scale(${checkScale})`}
            style={{ transformOrigin: "0 0" }}
          />
        </svg>
        <div style={{
          marginTop: 24, textAlign: "center",
          fontSize: 38, fontWeight: 900, color: COPPER, letterSpacing: 6,
          opacity: checkScale,
        }}>PROTEÇÃO DOCUMENTAL</div>
      </div>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 22. CommentBubbleCta — floating chat bubble with PATRIMÔNIO
// ──────────────────────────────────────────────────────────────────
export const CommentBubbleCta: React.FC<BaseProps & { keyword: string }> = ({
  startFrame, endFrame, keyword,
}) => {
  const { fps } = useVideoConfig();
  const { local, dur } = useRel(startFrame, endFrame);
  const entry = spring({ frame: local, fps, config: { damping: 12, stiffness: 200 } });
  const bounce = 1 + Math.sin(local / 8) * 0.06;
  const arrowPulse = 1 + Math.sin(local / 6) * 0.15;
  const exit = local > dur - fps * 0.5 ? interpolate(local, [dur - fps * 0.5, dur], [1, 0]) : 1;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: entry * exit }}>
      {/* bubble */}
      <div style={{
        position: "absolute", top: 700, left: "50%",
        transform: `translateX(-50%) scale(${entry * bounce})`,
      }}>
        <div style={{
          background: COPPER, color: GREEN_DARK,
          padding: "32px 56px", borderRadius: 32,
          fontSize: 96, fontWeight: 900, letterSpacing: 4,
          boxShadow: `0 16px 60px ${COPPER}66`,
          position: "relative",
        }}>
          {keyword}
          {/* tail */}
          <div style={{
            position: "absolute", bottom: -20, left: "50%", transform: "translateX(-50%) rotate(45deg)",
            width: 30, height: 30, background: COPPER,
          }} />
        </div>
      </div>
      {/* down arrow */}
      <div style={{
        position: "absolute", top: 1100, left: "50%",
        transform: `translateX(-50%) scale(${arrowPulse})`,
        fontSize: 88, color: COPPER,
      }}>↓</div>
      <div style={{
        position: "absolute", top: 1230, left: 0, right: 0, textAlign: "center",
        fontSize: 32, color: BEIGE, letterSpacing: 3, fontWeight: 900,
      }}>COMENTE NOS COMENTÁRIOS</div>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────────
// 23. HighlighterUnderline — copper marker stroke
// ──────────────────────────────────────────────────────────────────
export const HighlighterUnderline: React.FC<BaseProps> = ({ startFrame, endFrame }) => {
  const { local, dur } = useRel(startFrame, endFrame);
  const draw = interpolate(local, [0, dur * 0.5], [0, 1], { extrapolateRight: "clamp", easing: cubicOut });
  const exit = local > dur * 0.7 ? interpolate(local, [dur * 0.7, dur], [1, 0]) : 1;
  return (
    <div style={{
      position: "absolute", bottom: 280, left: "10%", right: "10%",
      height: 12, background: COPPER, borderRadius: 6,
      transform: `scaleX(${draw})`, transformOrigin: "left",
      opacity: 0.65 * exit,
    }} />
  );
};

// ──────────────────────────────────────────────────────────────────
// MASTER DISPATCHER
// ──────────────────────────────────────────────────────────────────
export type RichOverlayDef = {
  kind: string;
  start: number; // seconds
  end: number;   // seconds
  [key: string]: any;
};

export const RichOverlayRenderer: React.FC<{ overlay: RichOverlayDef; fps: number }> = ({
  overlay, fps,
}) => {
  // Inside Series.Sequence, useCurrentFrame() returns LOCAL frame (relative to sequence start).
  // So pass startFrame=0 to the inner components and let them compute time from there.
  const durationFrames = Math.round((overlay.end - overlay.start) * fps);
  const base = { startFrame: 0, endFrame: durationFrames };
  const k = overlay.kind;

  if (k === "stamp_brand") return <StampBrand {...base} text={overlay.text} position={overlay.position} />;
  if (k === "roman_scroll_wipe") return <RomanScrollWipe {...base} direction={overlay.direction} />;
  if (k === "roman_columns_bg") return <RomanColumnsBg {...base} opacity={overlay.opacity} />;
  if (k === "year_caption") return <YearCaption {...base} text={overlay.text} position={overlay.position} />;
  if (k === "vespasian_bust") return <VespasianBust {...base} position={overlay.position} />;
  if (k === "roman_latrine") return <RomanLatrine {...base} />;
  if (k === "gold_coin_drop") return <GoldCoinDrop {...base} land_at={overlay.land_at !== undefined ? Math.round((overlay.land_at - overlay.start) * fps) : undefined} />;
  if (k === "cinematic_title") return <CinematicTitle {...base} text={overlay.text} subtitle={overlay.subtitle} font_family={overlay.font_family} position={overlay.position} />;
  if (k === "code_document") return <CodeDocument {...base} article={overlay.article} title={overlay.title} />;
  if (k === "highlighter_underline") return <HighlighterUnderline {...base} />;
  if (k === "split_comparison") return <SplitComparison {...base} left_icon={overlay.left_icon} right_icon={overlay.right_icon} left_label={overlay.left_label} right_label={overlay.right_label} />;
  if (k === "merge_into_keyword") return <MergeIntoKeyword {...base} text={overlay.text} />;
  if (k === "stf_stamp") return <STFStamp {...base} text={overlay.text} />;
  if (k === "ticker_resp") return <TickerResp {...base} items={overlay.items} />;
  if (k === "scale_of_justice") return <ScaleOfJustice {...base} left_weight={overlay.left_weight} right_weight={overlay.right_weight} />;
  if (k === "context_tags") return <ContextTags {...base} tags={overlay.tags} />;
  if (k === "counter_number") return <CounterNumber {...base} from={overlay.from} to={overlay.to} suffix={overlay.suffix} subtitle={overlay.subtitle} />;
  if (k === "data_network") return <DataNetwork {...base} node_count={overlay.node_count} />;
  if (k === "mismatch_cards") return <MismatchCards {...base} declared_label={overlay.declared_label} declared_value={overlay.declared_value} actual_label={overlay.actual_label} actual_value={overlay.actual_value} />;
  if (k === "tributavel_stamp") return <TributavelStamp {...base} text={overlay.text} />;
  if (k === "warm_shift_pivot") return <WarmShiftPivot {...base} />;
  if (k === "tribotax_shield") return <TriboShield {...base} show_orbit={overlay.show_orbit} />;
  if (k === "comment_bubble_cta") return <CommentBubbleCta {...base} keyword={overlay.keyword} />;

  // ─── New kinds (Remotion package-backed overlays) ───────────────────────────
  if (k === "transition_scene") return <TransitionScene
    {...base}
    presentation={overlay.presentation}
    direction={overlay.direction}
    duration_ms={overlay.duration_ms}
    from_text={overlay.from_text}
    to_text={overlay.to_text}
    from_bg={overlay.from_bg}
    to_bg={overlay.to_bg}
    from_fg={overlay.from_fg}
    to_fg={overlay.to_fg}
  />;
  if (k === "audio_waveform") return <AudioWaveform
    {...base}
    audio_src={overlay.audio_src}
    bars={overlay.bars}
    color={overlay.color}
    position={overlay.position}
    height_px={overlay.height_px}
    smoothing={overlay.smoothing}
    frequency_range={overlay.frequency_range}
  />;
  if (k === "lottie") return <LottieScene
    {...base}
    lottie_src={overlay.lottie_src}
    position={overlay.position}
    scale={overlay.scale}
    loop={overlay.loop}
  />;
  if (k === "rive") return <RiveScene
    {...base}
    rive_src={overlay.rive_src}
    artboard={overlay.artboard}
    state_machine={overlay.state_machine}
    position={overlay.position}
    size={overlay.size}
  />;
  if (k === "three_reveal") return <ThreeReveal
    {...base}
    glb={overlay.glb}
    rotation_speed={overlay.rotation_speed}
    auto_rotate={overlay.auto_rotate}
    camera_z={overlay.camera_z}
    scale={overlay.scale}
    background_color={overlay.background_color}
    env_preset={overlay.env_preset}
  />;
  if (k === "motion_blur") return <MotionBlurOverlay
    {...base}
    mode={overlay.mode}
    child_text={overlay.child_text}
    font_size={overlay.font_size}
    color={overlay.color}
    trail_layers={overlay.trail_layers}
    lag_in_frames={overlay.lag_in_frames}
    shutter_angle={overlay.shutter_angle}
  />;
  if (k === "noise_background") return <NoiseBackground
    {...base}
    mode={overlay.mode}
    intensity={overlay.intensity}
    scale={overlay.scale}
    color_a={overlay.color_a}
    color_b={overlay.color_b}
    speed={overlay.speed}
    cell_size={overlay.cell_size}
  />;
  if (k === "shape_morph") return <ShapeMorph
    {...base}
    from_shape={overlay.from_shape}
    to_shape={overlay.to_shape}
    size={overlay.size}
    stroke_color={overlay.stroke_color}
    fill_color={overlay.fill_color}
    stroke_width={overlay.stroke_width}
    position={overlay.position}
    stroke_draw_seconds={overlay.stroke_draw_seconds}
  />;

  return null;
};
