# Remotion Feature Catalog

Complete map of Remotion primitives and packages, with explicit status: **USED** (already in skill), **ADDED** (new in this skill upgrade), **AVAILABLE** (available but not yet in templates — adopt as needed), **OUT OF SCOPE** (deliberately not used).

**Rule:** If a feature isn't listed here, it doesn't exist in this skill. Don't invent. If you need something not listed, propose an alternative from the catalog or escalate to Gabriel.

---

## Core Primitives

| Primitive | Status | Purpose |
|---|---|---|
| `<Composition>` | USED | Register video composition. One per top-level reel. |
| `<Sequence>` | USED | Time-shift child components by frame offset. |
| `<Series>` / `<Series.Sequence>` | AVAILABLE | Auto-sequence segments to play one after another. Use when manual `from=` math is brittle. |
| `<AbsoluteFill>` | USED | Full-screen absolute div. Layer overlays. |
| `<Loop>` | AVAILABLE | Repeat content N times or infinitely. Use for repeating elements (e.g. tickers). |
| `<Freeze>` | AVAILABLE | Freeze children at a specific frame. Use for end cards. |
| `<Video>` | DEPRECATED | Use `<OffthreadVideo>` instead for server-side rendering. |
| `<OffthreadVideo>` | USED | Off-thread video rendering — faster, fewer artifacts. |
| `<Audio>` | USED | Frame-accurate audio with volume/trim/playbackRate. |
| `<Img>` | USED | Image with guaranteed load-before-render. |
| `<Still />` | ADDED | Single-frame composition. Used for auto thumbnails (`renderStill()`). |
| `<IFrame>` | OUT OF SCOPE | External web content. Not useful for video reels. |

## Timing & Animation Hooks

| Hook/fn | Status | Purpose |
|---|---|---|
| `useCurrentFrame()` | USED | Current frame (absolute or sequence-relative). |
| `useVideoConfig()` | USED | `{ width, height, fps, durationInFrames }`. |
| `interpolate()` | USED | Map input range → output range, with easing. |
| `spring()` | USED | Physics-based animation (damping/stiffness/mass). |
| `random(seed)` | AVAILABLE | Deterministic pseudo-random. Use when overlay needs randomness reproducible across renders. |
| `measureSpring(fps, config)` | AVAILABLE | Frames needed for spring to settle. Use to plan exact overlay duration. |
| `interpolateColors(t, [a, b], [c1, c2])` | AVAILABLE | Smooth color transitions. |
| `Easing.bezier/back/bounce/elastic/...` | USED (partial) | Easing functions for `interpolate`. Full library available. |
| `delayRender()` / `continueRender()` | USED | Pause render until async work completes. |
| `cancelRender(error)` | AVAILABLE | Cancel render on irrecoverable error. Use in `delayRender` callbacks. |

## Metadata & Data-Driven

| Feature | Status | Purpose |
|---|---|---|
| `defaultProps` on `<Composition>` | USED | Initial props for composition. |
| `calculateMetadata({ props })` | ADDED | Derive `durationInFrames`/`fps`/dimensions from props at render time. Required for data-driven videos. |
| `schema` (Zod) | ADDED | Type-safe props + auto-generated Studio UI controls. |
| `@remotion/zod-types` | ADDED | Custom Zod types for Remotion (`zColor`, `zStaticFile`). |
| `staticFile(path)` | USED | Convert relative path → absolute for `<Img>`/`<Audio>`/`<Video>`. |
| `getStaticFiles()` | AVAILABLE | Enumerate files in `public/`. Use to auto-discover assets. |
| `watchStaticFile(path, cb)` | AVAILABLE | Hot-reload on asset change. Studio-only. |
| `prefetch(url)` | AVAILABLE | Preload asset before render to avoid stalls. |
| `getRemotionEnvironment()` | AVAILABLE | Distinguish `studio` / `rendering` / `player`. Use for environment-specific code. |

## Specialized Packages

| Package | Status | Purpose | Template in this skill |
|---|---|---|---|
| `@remotion/transitions` | ADDED | Named transitions (fade/slide/wipe/cube/clock-wipe) via `<TransitionSeries>`. | `TransitionScene.tsx` |
| `@remotion/captions` | AVAILABLE | Caption components with word-level timing. (We use custom `KineticCaption` for now.) | — |
| `@remotion/install-whisper-cpp` | OUT OF SCOPE | Whisper.cpp installer. We use `mlx-whisper` directly. | — |
| `@remotion/media-utils` | ADDED | `useAudioData`, `visualizeAudio`, audio waveform extraction. | `AudioWaveform.tsx` |
| `@remotion/lottie` | ADDED | Render Lottie/After Effects animations. | `LottieScene.tsx` |
| `@remotion/rive` | ADDED | Render Rive `.riv` interactive vector animations. | `RiveScene.tsx` |
| `@remotion/three` | ADDED | React Three Fiber 3D in video. Useful for Vhoe aircraft reveals, TriboTax 3D infographics. | `ThreeReveal.tsx` |
| `@remotion/skia` | AVAILABLE | High-perf 2D via Skia. Use for complex procedural drawing. | — |
| `@remotion/shapes` | ADDED | SVG primitive shapes (circle, polygon, star, etc.). | `ShapeMorph.tsx` |
| `@remotion/paths` | ADDED | SVG path manipulation, morphing, stroke animation. | `ShapeMorph.tsx` |
| `@remotion/motion-blur` | ADDED | Trail/blur HOCs for cinematic movement. | `MotionBlurOverlay.tsx` |
| `@remotion/noise` | ADDED | Perlin/simplex noise generators. | `NoiseBackground.tsx` |
| `@remotion/google-fonts` | ADDED | Bundle Google Fonts — zero network delay at render. | `templates/components/fonts.ts` |
| `@remotion/layout-utils` | AVAILABLE | Dynamic layout helpers (text measurement, fit). | — |
| `@remotion/animation-utils` | AVAILABLE | CSS animation property helpers. | — |
| `@remotion/gif` | AVAILABLE | Render animated GIFs frame-accurate. | — |
| `@remotion/tailwind-v4` | ADDED (opt-in) | Tailwind v4 CSS integration. Enable via `--with-tailwind` in `build_remotion.py`. | — |
| `@remotion/enable-scss` | OUT OF SCOPE | SCSS preprocessor. Not needed (Tailwind covers utility CSS). | — |
| `@remotion/player` | ADDED | Embeddable React player. Used by `preview_player.py` for client approval URLs. | — |
| `@remotion/studio` | USED | Interactive Studio (`npx remotion studio`). | — |
| `@remotion/lambda` | OUT OF SCOPE | AWS Lambda rendering. Local-only by user decision. | — |
| `@remotion/cloudrun` | OUT OF SCOPE | GCP Cloud Run rendering. Local-only. | — |

## Transitions (built-in)

Used via `<TransitionSeries.Sequence>` + `<TransitionSeries.Transition>`:

| Transition | Function | Use |
|---|---|---|
| Fade | `fade()` | Cross-fade between scenes |
| Slide | `slide({ direction: "from-left"|"from-right"|"from-top"|"from-bottom" })` | Slide one over the other |
| Wipe | `wipe({ direction })` | Wipe transition |
| Flip | `flip({ direction })` | 3D flip |
| Cube | `cube({ direction })` | 3D cube rotation |
| Clock-wipe | `clockWipe({ width, height })` | Radial clock-hand reveal |
| None | `none()` | Hard cut (rare — most cuts handled at V1 level) |

Timing: `linearTiming({ durationInFrames })` or `springTiming({ config })`.

## Rendering & CLI

| Command/API | Status | Purpose |
|---|---|---|
| `npx remotion render <id> <out>` | USED | Standard render. |
| `npx remotion still <id> <out.png>` | ADDED | Render single frame as image. Used by `render_thumbnail.py`. |
| `npx remotion studio` | USED | Interactive Studio dev server. |
| `renderMedia()` (Node API) | AVAILABLE | Programmatic render. We use CLI for now. |
| `renderStill()` (Node API) | ADDED | Programmatic still render. |
| `bundle()` | AVAILABLE | Bundle project for server-side render. |
| `getCompositions()` / `selectComposition()` | AVAILABLE | List/select compositions from a bundle. |
| `--scale=2` flag | USED | Supersample to fix sub-pixel aliasing in SVG (see [known-bugs.md](./known-bugs.md)). |
| `--concurrency=N` | USED | Parallelize frame encoding. |
| `--props='{...}'` | ADDED | Pass props to composition. Used by `batch_data_driven.py`. |

## Performance Optimization

| Technique | Status | Use |
|---|---|---|
| `<OffthreadVideo>` vs `<Video>` | USED | Always prefer Offthread for rendering. |
| `--scale=2` | USED | Supersample for SVG/text. Trade render time for clean edges. |
| `prefetch()` | AVAILABLE | Preload assets before scene starts. |
| `delayRender()` + `continueRender()` | USED | Block frame until async ready. |
| Composition splitting (one per overlay) | USED | Required for V2 isolation via `export_overlays.py`. |

## Type-Safe Props (Zod)

Pattern (added in this skill upgrade — see `Root.tsx.tmpl`):

```tsx
import { z } from "zod";
import { zColor } from "@remotion/zod-types";

const reelPropsSchema = z.object({
  title: z.string(),
  hookText: z.string().optional(),
  brandColor: zColor(),
  captionStyle: z.enum(["tiktok", "broadcast", "minimal"]),
  durationMs: z.number().min(1000).max(600000),
});

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    schema={reelPropsSchema}
    defaultProps={{ ... }}
    calculateMetadata={({ props }) => ({
      durationInFrames: Math.ceil((props.durationMs / 1000) * 30),
      fps: 30,
      width: 1080,
      height: 1920,
    })}
  />
);
```

Benefits:
- Studio shows sliders, color pickers, dropdowns automatically.
- Wrong-typed props caught at runtime with helpful messages.
- `calculateMetadata` enables data-driven videos (`--props='{"title":"...",...}'`).

## Common Patterns

### Data-driven (CSV → N reels)
Combine `defaultProps` + `calculateMetadata` + CLI `--props`. Iterate over rows of a CSV/JSON, render one composition per row with different props. See [data-driven-videos.md](./data-driven-videos.md).

### Audio-reactive visuals
`useAudioData(staticFile('voice.mp3'))` + `visualizeAudio({ frame, fps, audioData, numberOfSamples })` returns bar heights synced to playback. See [audio-reactive.md](./audio-reactive.md).

### 3D reveal
`<ThreeCanvas>` from `@remotion/three` + `useFrame` from `@react-three/fiber` synced to `useCurrentFrame()`. See [3d-and-lottie.md](./3d-and-lottie.md).

### Lottie embed
`<Lottie animationData={json}>` from `@remotion/lottie`. Drives playback from Remotion timeline automatically. See [3d-and-lottie.md](./3d-and-lottie.md).

### Embeddable player
`<Player component={Reel} durationInFrames={...} fps={30} compositionWidth={1080} compositionHeight={1920} controls />` in a static HTML page served by `preview_player.py`. See [preview-player.md](./preview-player.md).

### Auto thumbnail
`<Still id="reel-thumbnail" component={ThumbnailFrame} width={1080} height={1920} />` + `npx remotion still reel-thumbnail thumb.png --props=...`. Plan declares `thumbnail_frame_ms` to pick which moment of the reel to freeze.

### Branded template per client
Brand config (`.video-editor.json`) feeds into props via `build_remotion.py`. Zod schema validates. Components read `brand` prop and apply colors/fonts.

---

## Anti-patterns

These look attractive but cause bugs in this skill's pipeline:

- **`<Video>` instead of `<OffthreadVideo>`** — flicker artifacts during render.
- **Symlinks for `edit_plan.json`** — webpack ignores them. Use `cp`.
- **Underscore in `Composition.id`** — render fails immediately.
- **Straight alpha in ProRes** — must run `premultiply=inplace=1` filter post-render.
- **Custom random without seed** — overlay positions jitter between renders. Always seed.
- **Inline `import` of heavy package without delayRender** — slow Studio startup.

See [known-bugs.md](./known-bugs.md) for full failure catalog.
