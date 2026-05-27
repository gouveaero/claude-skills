# Component library

These TSX files live in `templates/components/` and are copied verbatim into
each per-reel project at `<output>/remotion/src/components/`. Edit them in place
to iterate; the next `build_remotion.py` run will overwrite, so port changes
back to `templates/` once finalized.

## VideoCut.tsx

Wraps `<OffthreadVideo>` with `startFrom`/`endAt` (frame-precise trim) plus a
CSS filter for color correction. Accepts:

| prop | type | notes |
|---|---|---|
| `clip` | `string` | Filename inside `public/clips/` |
| `sourceIn` | `number` | Seconds — converted to `Math.round(s * fps)` |
| `sourceOut` | `number` | Seconds — must be > sourceIn |
| `cssFilter` | `string?` | e.g. `"saturate(0.92) contrast(1.05)"` |

OffthreadVideo (vs. `<Video>`) renders frame-by-frame on the worker — required
for stable rendering of multiple cuts. Uses `objectFit: cover` so vertical
crops from horizontal sources work without distortion.

## KineticCaption.tsx

Per-word kinetic typography wrapper around `<Sequence>`. Each word in the
incoming `text` is classified (`keyword`/`emphasis`/`normal`) via
`classifyWord()` from `helpers.ts`, then animated with `spring` for a
scale-pop. Words stagger by 2 frames each.

| prop | type | notes |
|---|---|---|
| `text` | `string` | 1–4 words, will be uppercased |
| `start` | `number` | Seconds in final timeline |
| `end` | `number` | Seconds in final timeline |
| `emphasis` | `"keyword"\|"emphasis"\|"normal"?` | Force class for entire phrase |
| `style` | `"highlight_accent"\|"highlight_box"\|"minimal"?` | Default `highlight_accent` |
| `brandColors` | `BrandColors?` | Defaults from helpers; override per brand |
| `emphasisWords` | `Set<string>?` | Custom set of words to highlight |

Position is bottom-third (paddingBottom 26%) — adjust there if the brand wants
center or top placement.

## StatOverlay.tsx

Big-number flip for stats like `37%`, `+60%`, `R$2,3 mi`. Centered, copper
color, 360pt. Uses `spring` for entry pop and `interpolate` for fade-out.

| prop | type | notes |
|---|---|---|
| `text` | `string` | Big number/stat (kept as-is, not uppercased) |
| `subtext` | `string?` | Smaller line below |
| `start` | `number` | Seconds in final timeline |
| `end` | `number` | Seconds in final timeline |
| `brandColors` | `BrandColors?` | |
| `fontFamily` | `string?` | |

## LogoBug.tsx

Persistent watermark in a corner. Fades in over 15 frames, then holds. Pulls
the source path via `staticFile()` so the asset must live in `public/`
(`build_remotion.py` copies it there).

| prop | type | notes |
|---|---|---|
| `logoSrc` | `string?` | Path relative to `public/` |
| `position` | `"top-right"\|"top-left"\|"bottom-right"\|"bottom-left"?` | |
| `opacity` | `number?` | Default 0.7 |
| `size` | `number?` | px width — default 140 |

## helpers.ts

Pure utilities, no React.

- `classifyWord(word, emphasisWords?)` → `"keyword"|"emphasis"|"normal"`. Mirrors the davinci-skill regex (numbers, %, $, ★ → keyword; else lookup in `emphasisWords` set).
- `DEFAULT_EMPHASIS_WORDS` — ready-made set with TriboTax-friendly tax/agro words. Pass a custom Set for other clients.
- `DEFAULT_BRAND_COLORS` — fallback when no brand config supplies colors.
- `easings` — pre-built bezier curves (`outCubic`, `outBack`, `inOutQuad`, `punch`).
- `getStartFrame(seconds, fps)`, `secondsToFrames(seconds, fps)` — both `Math.round`.
