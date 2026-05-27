# Final Render — codec, CRF, concurrency reference

Phase 9 of the Remotion-only pipeline. Drives `npx remotion render` with appropriate
defaults per codec. Implemented in [`scripts/final_render.py`](../scripts/final_render.py).

## Quick reference — codec presets

```bash
# Default — H.264, max compatibility (Instagram, WhatsApp, browsers)
python3 final_render.py --remotion-dir <out>/remotion --out final.mp4 \
  --codec h264 --crf 18

# Smaller file (Instagram strips quality anyway, ~50% smaller)
final_render.py --codec h264 --crf 22

# H.265 / HEVC — smaller files, slower encode, less universal
final_render.py --codec h265 --crf 24

# ProRes 4444 — master/intermediate format, huge files but edit-friendly
final_render.py --codec prores --pixel-format yuv422p10le

# VP9 — YouTube-native, ~30% smaller than H.264 at same quality
final_render.py --codec vp9 --crf 30 --audio-codec libopus

# VP8 — legacy WebM (rarely needed)
final_render.py --codec vp8 --crf 10
```

## CRF (Constant Rate Factor) sweet spots

Lower = better quality, larger file. Logarithmic curve — 18 → 22 is a much smaller jump in size than 14 → 18.

| Codec | Visually lossless | Web quality | Compressed | Hard limit |
|---|---|---|---|---|
| H.264 | 17-18 | 21-23 | 26-28 | <30 visible |
| H.265 | 22-24 | 26-28 | 30-32 | <34 visible |
| VP9 | 28-30 | 32-34 | 36-38 | <40 visible |

**Default for this pipeline: H.264 CRF 18** — visually lossless, ~3-15 MB per minute, plays everywhere.

## Supersampling for clean SVG/text (`--scale`)

Chrome rasterizes at composition resolution (1080×1920 for 9:16). SVG paths and fine text get sub-pixel aliasing.

```bash
final_render.py --scale 2     # render at 2160×3840, downscale to 1080×1920
final_render.py --scale 4     # render at 4320×7680 (for very fine elements)
```

| Scale | Render time | Quality gain |
|---|---|---|
| 1 (default) | 1× | Baseline (acceptable for photo footage) |
| 2 | ~3× | Marked improvement on SVG/text edges |
| 4 | ~10× | Mostly for logos & micro-text |

If your reel is mostly photo/video with light text overlays: `scale=1` is fine.
If your reel is full of `RichOverlays` with SVG paths (StampBrand, ScaleOfJustice, STFStamp): `scale=2` is worth it.

## Concurrency

`--concurrency N` parallelizes frame encoding. Each parallel frame holds ~1 GB in Chrome.

| Setting | RAM peak | Speed gain |
|---|---|---|
| `--concurrency 1` | ~1.5 GB | baseline |
| `--concurrency 4` | ~5 GB | ~3× faster |
| `--concurrency 8` | ~9 GB | ~5× faster |
| `--concurrency 16` | ~17 GB | ~7× faster (diminishing returns) |

Remotion's default is half your CPU cores. Override only if RAM is constrained or you want to leave headroom for other work.

## Audio settings

| Setting | Default | When to override |
|---|---|---|
| `--audio-codec` | `aac` (h264/h265), `libopus` (vp8/vp9) | Rarely |
| `--audio-bitrate` | `192k` | Bump to `256k` for music-heavy reels |
| `--enforce-audio-track` | enabled | Always keep for Instagram/TikTok (they refuse muted MP4s) |

## Data-driven render (props per call)

```bash
final_render.py --props '{"title":"SU-35 Flanker-E","brandColor":"#8B3A1F","durationMs":42000}'
```

The composition's Zod schema validates the props. Wrong types → fail-fast with a helpful error.

See [data-driven-videos.md](./data-driven-videos.md) for batch use.

## Render time benchmarks (Mac M2 Pro, default scale=1)

| Reel duration | Concurrency 4 | Concurrency 8 |
|---|---|---|
| 30s reel, 15 overlays | ~90s | ~60s |
| 60s reel, 25 overlays | ~3 min | ~2 min |
| 3 min reel, 50 overlays | ~12 min | ~8 min |
| 30s reel + ThreeReveal | ~6 min | ~5 min |

Three.js / Lottie scenes are render-bound — concurrency helps less.

## Anti-patterns

- **Render HQ first, skip proxy** — proxy is 30s and catches 95% of bugs. HQ is 5-30 min wasted if something is wrong.
- **`--scale 4` by default** — wastes time. Only when you can see aliasing in the proxy at scale=2.
- **Set `--concurrency 16` on a 16GB Mac** — Chrome OOM-kills mid-render. Match RAM.
- **`--audio-codec none`** — Instagram refuses. Always include audio (even if silent).
- **Codec ProRes for Instagram delivery** — Instagram re-encodes to H.264 anyway. Use ProRes only for editorial intermediates.

## See also

- [data-driven-videos.md](./data-driven-videos.md) — batch render with `--props` per row
- [known-bugs.md](./known-bugs.md) — Remotion-side render bugs + supersampling rationale
- [workflow.md](./workflow.md) — full pipeline context
