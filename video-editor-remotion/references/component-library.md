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

## TransitionScene.tsx (NEW)

Drop-in named transition between two cards rendered in the same overlay slot.
Built on `@remotion/transitions` with `<TransitionSeries>`.

| prop | type | notes |
|---|---|---|
| `presentation` | `"fade"\|"slide"\|"wipe"\|"flip"\|"clock-wipe"` | Transition kind |
| `direction` | `"from-left"\|"from-right"\|"from-top"\|"from-bottom"` | For slide/wipe/flip |
| `duration_ms` | `number?` | Default 400 |
| `from_text`, `to_text` | `string` | Card text content |
| `from_bg`, `to_bg`, `from_fg`, `to_fg` | `string?` | Card colors |

## AudioWaveform.tsx (NEW)

Vertical bars reactive to audio at current frame. Uses `useAudioData` +
`visualizeAudio` from `@remotion/media-utils`. See [audio-reactive.md](./audio-reactive.md).

| prop | type | notes |
|---|---|---|
| `audio_src` | `string` | Path relative to `public/` |
| `bars` | `number?` | Default 48 |
| `color` | `string?` | Default `#B87333` |
| `position` | `"top"\|"bottom"\|"center"` | Default `bottom` |
| `height_px` | `number?` | Max bar height, default 200 |
| `smoothing` | `0..1` | Default 0.7 |
| `frequency_range` | `"full"\|"voice"\|"bass"` | FFT bin slice |

## LottieScene.tsx (NEW)

Embed After Effects animations (`.json` from Bodymovin export). Uses `@remotion/lottie`.

| prop | type | notes |
|---|---|---|
| `lottie_src` | `string` | Path relative to `public/animations/` |
| `position` | `"center"\|"top-right"\|...` | Default `center` |
| `scale` | `number?` | Default 1 |
| `loop` | `boolean?` | Default false |

## RiveScene.tsx (NEW)

Embed Rive interactive vector animations (`.riv` files). Uses `@remotion/rive`.

| prop | type | notes |
|---|---|---|
| `rive_src` | `string` | Path relative to `public/rive/` |
| `artboard` | `string?` | Artboard name within the .riv |
| `state_machine` | `string?` | State machine name |
| `position` | `"center"\|"top-right"\|...` | Default `center` |
| `size` | `number?` | Canvas size px, default 600 |

## ThreeReveal.tsx (NEW)

3D model rotation using `@remotion/three` + `@react-three/fiber` + `@react-three/drei`.
For aircraft reveals (Vhoe), 3D infographics (TriboTax), product showcases.
See [3d-and-lottie.md](./3d-and-lottie.md).

| prop | type | notes |
|---|---|---|
| `glb` | `string` | Path relative to `public/models/` |
| `rotation_speed` | `number?` | Radians per second, default 0.6 |
| `auto_rotate` | `boolean?` | Default true |
| `camera_z` | `number?` | Default 5 |
| `scale` | `number?` | Default 1 |
| `background_color` | `string?` | Hex, default `#0A1A0F` |
| `env_preset` | `"sunset"\|"dawn"\|...` | Default `sunset` |

## MotionBlurOverlay.tsx (NEW)

Cinematic motion blur — `Trail` (stutter copies) or `CameraMotionBlur`.
Uses `@remotion/motion-blur`.

| prop | type | notes |
|---|---|---|
| `mode` | `"trail"\|"camera"` | Default `trail` |
| `child_text` | `string` | Text to apply effect to |
| `font_size` | `number?` | Default 200 |
| `color` | `string?` | Default `#B87333` |
| `trail_layers` | `number?` | Default 8 |
| `lag_in_frames` | `number?` | Default 2 |
| `shutter_angle` | `number?` | Default 180 (camera mode) |

## NoiseBackground.tsx (NEW)

Procedural noise overlays (perlin/simplex/film-grain). Uses `@remotion/noise`.

| prop | type | notes |
|---|---|---|
| `mode` | `"grain"\|"flow"\|"static"` | Default `flow` |
| `intensity` | `0..1` | Default 0.4 |
| `scale` | `number?` | Noise frequency, default 4 |
| `color_a`, `color_b` | `string?` | Gradient endpoints |
| `speed` | `number?` | Animation speed, default 0.5 |
| `cell_size` | `number?` | Grid cell px, default 40 |

## ShapeMorph.tsx (NEW)

Geometric shape morphing with stroke-draw entry. Uses `@remotion/shapes` +
`@remotion/paths`.

| prop | type | notes |
|---|---|---|
| `from_shape` | `"circle"\|"triangle"\|"rect"\|"star"\|"polygon"` | Default `circle` |
| `to_shape` | `same` | Default `star` |
| `size` | `number?` | Default 320 |
| `stroke_color`, `fill_color` | `string?` | |
| `stroke_width` | `number?` | Default 8 |
| `position` | `"center"\|"top-right"\|...` | Default `center` |
| `stroke_draw_seconds` | `number?` | Default 1.0 |

## fonts.ts (NEW)

Centralized Google Fonts loading via `@remotion/google-fonts`. Idempotent helpers.

Available exports:
- `loadInter(weights?)`, `loadPlayfair(weights?)`, `loadCinzel(weights?)`,
  `loadJetBrains(weights?)`, `loadBebasNeue()`, `loadMontserrat(weights?)`
- Stack constants: `BRAND_FONT_STACK`, `SERIF_TITLE_STACK`,
  `SERIF_CINZEL_STACK`, `MONO_STACK`
- `preloadCommonFonts()` — called from `Root.tsx` at module load

## helpers.ts

Pure utilities, no React.

- `classifyWord(word, emphasisWords?)` → `"keyword"|"emphasis"|"normal"`. Mirrors the davinci-skill regex (numbers, %, $, ★ → keyword; else lookup in `emphasisWords` set).
- `DEFAULT_EMPHASIS_WORDS` — ready-made set with TriboTax-friendly tax/agro words. Pass a custom Set for other clients.
- `DEFAULT_BRAND_COLORS` — fallback when no brand config supplies colors.
- `easings` — pre-built bezier curves (`outCubic`, `outBack`, `inOutQuad`, `punch`).
- `getStartFrame(seconds, fps)`, `secondsToFrames(seconds, fps)` — both `Math.round`.
