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

## Type-safe data-driven render (added in upgrade)

```tsx
// Root.tsx
import { z } from "zod";
import { zColor } from "@remotion/zod-types";

const reelPropsSchema = z.object({
  title: z.string(),
  brandColor: zColor(),
  durationMs: z.number().min(1000).max(600000),
});

<Composition
  id="Reel"
  component={Reel}
  schema={reelPropsSchema}
  defaultProps={{ title: "", brandColor: "#B87333", durationMs: 30000 }}
  fps={30} width={1080} height={1920}
  calculateMetadata={({ props }) => ({
    durationInFrames: Math.ceil((props.durationMs / 1000) * 30),
  })}
/>
```

Then render N rows:

```bash
python3 ~/.claude/skills/video-editor/scripts/batch_data_driven.py \
  --data aeronaves.csv --remotion-dir <out>/remotion --out-dir <out>/batch/
```

See [data-driven-videos.md](./data-driven-videos.md).

## Three.js model reveal (added in upgrade)

```tsx
import { ThreeCanvas } from "@remotion/three";
import { useGLTF, Environment, OrbitControls } from "@react-three/drei";

const Model = ({ rotation }) => {
  const { scene } = useGLTF(staticFile("models/su-35.glb"));
  return <primitive object={scene} rotation={[0, rotation, 0]} />;
};

<ThreeCanvas camera={{ position: [0, 0, 5], fov: 50 }}>
  <ambientLight intensity={0.5} />
  <directionalLight position={[5, 5, 5]} />
  <Model rotation={(useCurrentFrame() / 30) * 0.6} />
  <Environment preset="sunset" />
</ThreeCanvas>
```

Full pattern in [`templates/components/ThreeReveal.tsx`](../templates/components/ThreeReveal.tsx). See [3d-and-lottie.md](./3d-and-lottie.md).

## Lottie embed (added in upgrade)

```tsx
import { Lottie } from "@remotion/lottie";

const [data, setData] = useState(null);
const [handle] = useState(() => delayRender("lottie"));
useEffect(() => {
  fetch(staticFile("animations/logo.json"))
    .then(r => r.json()).then(json => { setData(json); continueRender(handle); });
}, []);
if (!data) return null;
return <Lottie animationData={data} loop={false} />;
```

## Named transition between scenes (added in upgrade)

```tsx
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}>
    <SceneA />
  </TransitionSeries.Sequence>
  <TransitionSeries.Transition
    presentation={slide({ direction: "from-right" })}
    timing={linearTiming({ durationInFrames: 12 })}
  />
  <TransitionSeries.Sequence durationInFrames={90}>
    <SceneB />
  </TransitionSeries.Sequence>
</TransitionSeries>
```

## Render thumbnail (added in upgrade)

```bash
python3 ~/.claude/skills/video-editor/scripts/render_thumbnail.py \
  --remotion-dir <out>/remotion \
  --out <out>/thumbnail.png \
  --frame-ms 80000 \
  --title "TÍTULO DA CAPA"
```

Or via CLI directly:

```bash
npx remotion still reel-thumbnail thumb.png --frame=2400 --props='{"title":"X"}'
```

## Sharable preview player (added in upgrade)

```bash
python3 ~/.claude/skills/video-editor/scripts/preview_player.py \
  --remotion-dir <out>/remotion --port 8123
# Then: tailscale funnel 8123  (share public URL with client)
```

See [preview-player.md](./preview-player.md).

## Reference URLs

- Remotion 4 API: https://www.remotion.dev/docs/the-fundamentals
- `<TransitionSeries>`: https://www.remotion.dev/docs/transitions/transitionseries
- `spring()`: https://www.remotion.dev/docs/spring
- `interpolate()`: https://www.remotion.dev/docs/interpolate
- `<OffthreadVideo>`: https://www.remotion.dev/docs/offthreadvideo
