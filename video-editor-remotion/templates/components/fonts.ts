// Centralized font loading via @remotion/google-fonts.
// Imports here are bundled into the Remotion project — no network delay at render time.
// Add new fonts by adding the import + export entry below; build_remotion.py auto-includes this.
//
// Usage in components:
//   import { loadInter, loadPlayfair } from "./fonts";
//   const { fontFamily } = loadInter();
//   <div style={{ fontFamily, fontWeight: 900 }}>...</div>

import { loadFont as _loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as _loadPlayfairDisplay } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as _loadCinzel } from "@remotion/google-fonts/Cinzel";
import { loadFont as _loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as _loadBebasNeue } from "@remotion/google-fonts/BebasNeue";
import { loadFont as _loadMontserrat } from "@remotion/google-fonts/Montserrat";

// Each helper is idempotent — calling multiple times returns the same fontFamily.
export const loadInter = (weights: string[] = ["400", "700", "900"]) =>
  _loadInter("normal", { weights });

export const loadPlayfair = (weights: string[] = ["400", "700", "900"]) =>
  _loadPlayfairDisplay("normal", { weights });

export const loadCinzel = (weights: string[] = ["400", "700", "900"]) =>
  _loadCinzel("normal", { weights });

export const loadJetBrains = (weights: string[] = ["400", "700"]) =>
  _loadJetBrainsMono("normal", { weights });

export const loadBebasNeue = () => _loadBebasNeue("normal", { weights: ["400"] });

export const loadMontserrat = (weights: string[] = ["400", "700", "900"]) =>
  _loadMontserrat("normal", { weights });

// Convenience preset stacks used by the established components:
export const BRAND_FONT_STACK = "Inter, system-ui, sans-serif";
export const SERIF_TITLE_STACK = "'Playfair Display', Georgia, serif";
export const SERIF_CINZEL_STACK = "'Cinzel', 'Playfair Display', Georgia, serif";
export const MONO_STACK = "'JetBrains Mono', Menlo, Consolas, monospace";

// Call this once from Root.tsx (or any top-level component) to ensure fonts are bundled
// before any frame is rendered.
export const preloadCommonFonts = () => {
  loadInter();
  loadPlayfair();
};
