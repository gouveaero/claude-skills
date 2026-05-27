/**
 * helpers.ts — shared utilities for Remotion components.
 *
 * Mirrors the `_classify_word` logic from video-editor-davinci so that
 * keyword/emphasis word detection produces identical highlights across both
 * skills. Pass `emphasisWords` from the brand config to customize.
 */
import { Easing } from "remotion";

export type WordClass = "keyword" | "emphasis" | "normal";

const KEYWORD_RE = /^[\d★+\-]+%?$|%$|\$|^R\$/;

export const DEFAULT_EMPHASIS_WORDS = new Set<string>([
  "AGIOTA",
  "MULTA",
  "SELIC",
  "FALÊNCIA",
  "FALENCIA",
  "DÍVIDA",
  "DIVIDA",
  "ATIVA",
  "GOVERNO",
  "BRASILEIRO",
  "EMPRESÁRIO",
  "EMPRESARIO",
  "PUNIR",
  "PENHORA",
  "DIAGNÓSTICO",
  "DIAGNOSTICO",
]);

export function classifyWord(
  word: string,
  emphasisWords: Set<string> = DEFAULT_EMPHASIS_WORDS
): WordClass {
  const s = word.trim().toUpperCase().replace(/[.,!?]+$/, "");
  if (!s) return "normal";
  if (KEYWORD_RE.test(s) || s.includes("%") || s.includes("$")) return "keyword";
  if (/\d/.test(s)) return "keyword";
  if (emphasisWords.has(s)) return "emphasis";
  return "normal";
}

export const easings = {
  outCubic: Easing.bezier(0.33, 1, 0.68, 1),
  outBack: Easing.bezier(0.34, 1.56, 0.64, 1),
  inOutQuad: Easing.bezier(0.45, 0, 0.55, 1),
  punch: Easing.bezier(0.22, 1.61, 0.36, 1),
};

export function getStartFrame(timelineSeconds: number, fps: number): number {
  return Math.round(timelineSeconds * fps);
}

export function secondsToFrames(seconds: number, fps: number): number {
  return Math.round(seconds * fps);
}

export type BrandColors = {
  keyword: string;
  emphasis: string;
  normal: string;
  stroke: string;
};

export const DEFAULT_BRAND_COLORS: BrandColors = {
  keyword: "#B87333",
  emphasis: "#F5C83C",
  normal: "#FFFFFF",
  stroke: "#0A0A0A",
};

// Instagram Reels safe zones for 1080x1920 — measured from screenshots of real UI
// Top: avatar (~80px) + handle (~50px) + breathing → 220px
// Bottom: caption (~140px) + buttons row (~180px) + breathing → 350px
export const SAFE_ZONES_INSTAGRAM_REEL = {
  top: 220,
  bottom: 350,
  left: 60,
  right: 60,
} as const;
