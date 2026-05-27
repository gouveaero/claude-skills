# Remotion cookbook (snippets)

Quick patterns Gabriel-and-Claude reach for when iterating live in Studio.

## Make a word fade in left-to-right

```tsx
import { interpolate, useCurrentFrame } from "remotion";

const frame = useCurrentFrame();
const opacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });
const dx = interpolate(frame, [0, 12], [-40, 0], { extrapolateRight: "clamp" });
return <div style={{ opacity, transform: `translateX(${dx}px)` }}>{word}</div>;
```

## Add waveform sync (Audiogram-style)

```tsx
import { useAudioData, visualizeAudio } from "@remotion/media-utils";

const audioData = useAudioData(staticFile("music.mp3"));
const visualization = audioData ? visualizeAudio({
  fps, frame, audioData, numberOfSamples: 32,
}) : [];
return <div style={{ display: "flex", gap: 4 }}>{visualization.map((v, i) =>
  <div key={i} style={{ width: 8, height: 200 * v, background: "#B87333" }} />
)}</div>;
```

Install: `cd <remotion> && npm install @remotion/media-utils`.

## Cross-dissolve between two cuts

`@remotion/transitions` already powers Reel.tsx. To force a fade between cuts
N and N+1, set in `edit_plan.json`:

```json
"transitions": [
  { "after_cut_index": 4, "type": "fade", "duration_frames": 8 }
]
```

## Use Remotion's bundled whisper.cpp

```bash
cd <remotion>
npx remotion install whisper-cpp
node -e "import('@remotion/install-whisper-cpp').then(m => m.transcribe({...}))"
```

Use this fallback when `mlx-whisper` isn't available (non-Apple-Silicon).

## Render only a slice of frames (debugging)

```bash
npx remotion render Reel /tmp/scrub.mp4 --frames=0-90 --codec=h264
```

Useful when iterating just on the intro — saves render time.

## Pass dynamic props from CLI

```bash
npx remotion render Reel out/variant_a.mp4 --props='{"hookIndex": 0}' --codec=h264
```

The composition reads `defaultProps` merged with `--props`. To consume in a
component:

```tsx
export const Reel: React.FC<{ plan: Plan; brand: BrandConfig; hookIndex?: number }>
  = ({ plan, brand, hookIndex = 0 }) => {
  const hook = plan.hooks?.[hookIndex] ?? plan.hooks?.[0];
  // ...
};
```

`batch_render.py` automates this for CSV-driven variations.

## Fonts (Inter / Bebas Neue)

```tsx
import { loadFont } from "@remotion/google-fonts/Inter";
const { fontFamily } = loadFont();
// ...
<span style={{ fontFamily, fontWeight: 800 }}>{text}</span>
```

For local fonts, drop `.woff2` into `<remotion>/public/fonts/` and reference
via `@font-face` in `src/index.css`. Be sure to preload via `delayRender`/
`continueRender` so the render frame doesn't fire before the font loads.

## Speed up rendering

```bash
# Use all cores + lower-quality preview render
npx remotion render Reel /tmp/preview.mp4 --concurrency=8 --crf=28 --jpeg-quality=80

# Production render
npx remotion render Reel out/final.mp4 --concurrency=8 --crf=18 --enforce-audio-track
```

`--enforce-audio-track` ensures audio is encoded even if no clip in the
window has audio (Instagram refuses muted MP4s).

## Common errors

| Error | Fix |
|---|---|
| `Module not found: '@remotion/transitions'` | `cd <remotion> && npm install @remotion/transitions` |
| `Could not find composition with id 'Reel'` | Check `Root.tsx` has `<Composition id="Reel" .../>` |
| `Black frames around transitions` | Make sure `cuts.length >= 2` and the transition's `duration_frames > 0` |
| `Audio cuts off mid-word` | `endAt` is too early — extend `source_out` by ~0.1s |
| `Out of memory during render` | Lower `--concurrency` or render in chunks via `--frames` |

## Reference URLs

- Remotion 4 API: https://www.remotion.dev/docs/the-fundamentals
- `<TransitionSeries>`: https://www.remotion.dev/docs/transitions/transitionseries
- `spring()`: https://www.remotion.dev/docs/spring
- `interpolate()`: https://www.remotion.dev/docs/interpolate
- `<OffthreadVideo>`: https://www.remotion.dev/docs/offthreadvideo
