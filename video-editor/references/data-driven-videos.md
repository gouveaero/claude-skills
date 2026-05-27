# Data-Driven Videos — CSV/JSON → N Reels

Generate many videos from a spreadsheet. One row = one reel. Each render gets the row's fields as props; `calculateMetadata` in `Root.tsx` derives duration per-row.

## When to use

- 50 Vhoe reels from `aeronaves.csv` (one per aircraft, swapping `glb`, `title`, `voice_src`, `narration_seconds`)
- 20 TriboTax reels from `precedentes.csv` (one per legal precedent — different article number, court, ruling text)
- 100 Telesapiens course-promo reels from a catalog
- 12 anniversary cards from a `customers.csv`

## How it works

1. **Compose your `Reel`** so it accepts the row fields as props. The Zod schema in `Root.tsx` validates each prop set.
2. **Build the Remotion project** once (`build_remotion.py`). The schema is now embedded; data only changes at render time.
3. **Run `batch_data_driven.py`** with your data file. It calls `npx remotion render --props='{...}'` once per row, in parallel.

## Example: Vhoe aeronaves.csv

```csv
slug,title,glb,voice_src,narration_seconds,brandColor,hookText
su-35,SU-35 Flanker-E,models/su-35.glb,voice/su35.mp3,42,#8B3A1F,"FOI O PIOR PESADELO DA RÚSSIA"
f-15ex,F-15EX Eagle II,models/f-15ex.glb,voice/f15ex.mp3,38,#0A1A0F,"A ÁGUIA QUE NÃO ENVELHECE"
rafale,Rafale F4,models/rafale.glb,voice/rafale.mp3,45,#1F4D2C,"O CAÇA QUE A FRANÇA ESCONDIA"
```

Required Reel composition props (Zod-validated):
- `glb: string` → passed to `<ThreeReveal glb={...} />`
- `title: string` → passed to `<CinematicTitle text={...} />`
- `voice_src: string` → passed to `<Audio src={staticFile(voice_src)} />`
- `narration_seconds: number` → drives `durationMs = narration_seconds * 1000`
- `brandColor: string` (hex) → tints overlays
- `hookText: string` → optional opening hook

Place all referenced files (`models/*.glb`, `voice/*.mp3`) in `<remotion>/public/` before running.

## Running the batch

```bash
python3 ~/.claude/skills/video-editor/scripts/batch_data_driven.py \
  --data ~/Videos/vhoe/aeronaves.csv \
  --remotion-dir ~/Videos/vhoe/output/remotion \
  --out-dir ~/Videos/vhoe/output/batch/ \
  --concurrency 2 \
  --filename-template "{slug}-vhoe.mp4"
```

## Tuning concurrency

- `--concurrency 1` — sequential, safest. ~3 min per 60s reel on M2.
- `--concurrency 2` — recommended. RAM usage ~5GB peak. ~1.7× speedup.
- `--concurrency 4` — only if you have 16+ GB free RAM and lots of cores.

Each Remotion render spawns its own Chrome headless instance (~2GB). Going past `concurrency=4` rarely helps.

## Filename templates

`--filename-template` supports any row field as `{field}` placeholders, plus `{slug}` (auto-derived) and `{idx}` (zero-padded index).

Examples:
- `"{slug}.mp4"` → `su-35.mp4`, `f-15ex.mp4`
- `"{idx:03d}-{slug}.mp4"` → `000-su-35.mp4`, `001-f-15ex.mp4`
- `"vhoe/{brand}/{slug}-final.mp4"` → nested folders

## Type-safe props (Zod)

The composition's Zod schema catches bad data immediately:

```tsx
const reelPropsSchema = z.object({
  glb: z.string(),
  title: z.string().min(1).max(80),
  narration_seconds: z.number().min(5).max(180),
  brandColor: zColor(),
  // ...
});
```

If your CSV has `narration_seconds=999` and the schema caps at 180, the render fails fast with a clear error pointing to that row. No silent malformed outputs.

## Limiting / testing

`--limit 3` processes only the first 3 rows. Use for smoke tests:

```bash
python3 batch_data_driven.py --data aeronaves.csv ... --limit 3
```

## Anti-patterns

- **Don't read external files from inside the composition** at render time — use `<Img>`, `<Audio>`, `<OffthreadVideo>` with `staticFile()`. Anything else stalls the renderer or fails on Lambda.
- **Don't put narration_seconds in the row but ignore it in `calculateMetadata`** — duration mismatch causes audio to cut mid-word.
- **Don't share mutable JS objects between rows** — `defaultProps` is per-Composition, not per-render. Pass everything explicitly via `--props`.

## See also

- [remotion-feature-catalog.md](./remotion-feature-catalog.md) — `calculateMetadata`, Zod schemas
- [audio-reactive.md](./audio-reactive.md) — adding audio waveforms driven by `voice_src`
- [3d-and-lottie.md](./3d-and-lottie.md) — using `<ThreeReveal glb={...}>` per-row
