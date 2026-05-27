---
name: video-editor-remotion
description: >
  Use when the user wants a fully automated end-to-end video pipeline that renders
  the final MP4 100% with Remotion — no CapCut, no DaVinci, no external NLE.
  Triggers: "render direto", "vídeo final automático", "sem CapCut", "pipeline 100% Remotion",
  "Remotion-only", "autonomous video render", "batch video rendering", "headless reel render",
  "data-driven video generation", "render N reels from CSV". For the CapCut-deliverable
  workflow with human polish step, use video-editor instead. For DaVinci Resolve,
  use video-editor-davinci.
---

# video-editor-remotion

100% Remotion video pipeline: raw clips → planned edit → final MP4. No CapCut export, no ProRes alpha post-processing, no NLE handoff. Human approval is on the proxy.mp4 before final HQ render.

## When to use this vs siblings

```
End-to-end auto / batch (50 reels from CSV) / no human NLE polish  →  /video-editor-remotion
CapCut deliverable + human polish step                              →  /video-editor
DaVinci Resolve project (color grading, longer-form)                →  /video-editor-davinci
```

**Use this when**: you trust the LLM-generated edit_plan, want fully automated rendering, or are running batch renders where opening CapCut N times is not viable.

**Use `/video-editor` instead when**: a human editor will polish in CapCut afterward (the typical workflow for client deliverables that need final aesthetic decisions).

**RELATED SKILLS:** [[vhoe-roteiro]] (input script for Vhoe reels), [[imagens-freepik]] (PNG generation), [[video-editor]] (sibling with CapCut deliverable), [[video-editor-davinci]] (sibling for DaVinci), [[carousel-generator]] (similar HTML→export paradigm).

## Quick start

```bash
# Once per machine — check deps (node, ffmpeg, mlx-whisper, anthropic):
python ~/.claude/skills/video-editor-remotion/scripts/check_setup.py

# Run pipeline (9 phases auto, human gate after preview, final MP4 out):
python ~/.claude/skills/video-editor-remotion/scripts/build_pipeline.py \
  --input ~/Videos/meu-projeto/brutos/ \
  --aspect 9:16 \
  --target-duration 30
```

Project overrides live in `.video-editor.json` anywhere up the directory tree.

## On activation, ask the user

1. **What do you have?** (raw clips, script/roteiro, partial project, or just an `edit_plan.json`?)
2. **Aspect ratio?** (9:16 Reels/TikTok/Shorts or 16:9 YouTube)
3. **Target duration?** (seconds)
4. **Codec preference?** (H.264 default; H.265 for smaller files; ProRes for master quality)

## Pipeline overview (9 phases — streamlined vs CapCut sibling)

| # | Phase | What it does |
|---|------|-----------|
| 1 | Setup | Transcode HEVC/4K → H.264 1080p (proxy) — Remotion seeks frame-accurate; transcode mostly for size reduction. |
| 2 | Transcribe | mlx-whisper word-level on all clips |
| 3 | Filter raws | Select relevant clips (transcript + visual fallback) |
| 4 | Plan edit | Claude generates `edit_plan.json` (cuts, SFX, zooms, overlays, captions, music) |
| 5 | Request assets | Verify logos/images — block if missing |
| 6 | Build Remotion | Scaffold Node project + resolve SFX + copy files to `public/sfx/` |
| 7 | Preview | Remotion Studio (hot-reload) + proxy MP4 in parallel |
| **7.5** | **Visual Review** | Auto-QA: agent reviews extracted frames per `rich_overlay`, fixes `RichOverlays.tsx` BEFORE human sees it |
| **8** | **HUMAN GATE** | Review proxy.mp4 and approve before final render (skip with `--autonomous`) |
| **9** | **Final render** | `npx remotion render Reel final.mp4 --codec=h264 --crf=18`. MP4 self-contained. |
| 9.5 | (opt) Thumbnail | `render_thumbnail.py --frame-ms 80000` → cover image for Instagram |

For full phase details: [workflow.md](./references/workflow.md).

## Deliverable

A single self-contained `final.mp4` (1080×1920 H.264, ~3-15MB per minute). No `capcut_package/`, no draft files, no "Link media" reconnection. Upload-ready.

Plus optionally:
- `thumbnail.png` (1080×1920 cover image)
- `preview/` (bundled `@remotion/player` static site for client review)

## Red Flags — STOP and reconsider

- **"Skip the visual review loop"** → overlays <2s slip past eyeball review. Loop is mandatory until iteration #5 or all PASS.
- **"Render final without proxy approval"** → 5-30 min wasted render time if anything is wrong. Always check `proxy.mp4` first (unless `--autonomous`).
- **"Underscore in Composition.id"** → render fails immediate. Use hyphens.
- **"Symlink edit_plan.json → remotion/src/"** → webpack ignores symlinks. Use `cp`.
- **"Draw SVG by hand for figura humana / balança / brasão"** → amateur output. Always PNG-first ([overlay-density.md](./references/overlay-density.md)). Hard rule from TriboTax 2026-05-12.
- **"Invent a Remotion feature"** → consult [remotion-feature-catalog.md](./references/remotion-feature-catalog.md) first. If not there, propose existing alternative.
- **"H.265 by default"** → Instagram + WhatsApp re-encode H.265 anyway; H.264 CRF 18 plays everywhere. H.265 only if file size matters.

## Rationalization table

| Excuse | Reality |
|--------|---------|
| "Visual review is overkill, I'll just watch proxy" | Overlays <2s slip past. Loop is mandatory. |
| "Skip proxy, render HQ directly" | HQ render is 5-30min. Proxy is 30s + catches 95% of bugs. |
| "PNG is good enough, I'll just draw SVG" | Amateur output. PNG-first is non-negotiable. |
| "I can invent a Remotion feature" | No. Consult `remotion-feature-catalog.md`. |
| "1 overlay every 20s is plenty" | Minimum 1 per 8-10s (see overlay-density.md). |
| "Use `<Video>` instead of `<OffthreadVideo>`" | Flicker artifacts. Always Offthread. |

## Output structure

```
<input_dir>/../output/<reel-name>/
├── clips_proxy/                ← proxies H.264 1080p (input for Reel.tsx)
├── transcripts.json            ← word-level transcripts
├── clips_selecionados.json     ← filter result
├── edit_plan.json              ← SOURCE OF TRUTH (edit to iterate)
├── edit_plan_resolved.json     ← plan with SFX paths resolved (auto)
├── assets_needed.json          ← external assets manifest
├── remotion/
│   ├── public/
│   │   ├── clips/              ← cuts brutos
│   │   ├── icons/              ← PNGs from icon library
│   │   ├── sfx/                ← SFX files copied here for bundling
│   │   ├── models/             ← .glb files (if three_reveal used)
│   │   ├── animations/         ← .json Lottie
│   │   └── rive/               ← .riv files
│   └── src/
│       ├── Root.tsx            ← Compositions with Zod schemas
│       ├── Reel.tsx            ← Main composition (V1 + V2+ + SFX <Audio>)
│       └── ReelThumbnail.tsx   ← <Still> composition
├── proxy.mp4                   ← low-res preview (540×960 — phase 7)
├── final.mp4                   ← FINAL DELIVERABLE (1080×1920 H.264 — phase 9)
└── thumbnail.png               ← optional cover image
```

## SFX in Remotion (key difference from CapCut sibling)

SFX in `edit_plan.json.sfx[]` are resolved during `build_remotion.py`:
1. Category like `WOOSH` → concrete file via `sfx_index.json` + deterministic seed
2. File copied to `<remotion>/public/sfx/<filename>`
3. Plan's sfx entry gets a `file` field added (written to `edit_plan_resolved.json`)
4. `Reel.tsx` renders one `<Audio>` per sfx entry with `startFrom`, `volume`, optional `endAt`

Volume conversion: `volume_db: -10` → `linear: 0.316` (`10 ** (db / 20)`). All audio tracks mix linearly in Remotion's render output.

Duration caps (`SFX_DURATION_CAPS_MS` by category) are applied via `Sequence durationInFrames` — overlapping SFX of the same category get trimmed automatically.

## What's gone vs CapCut sibling

Removed in this fork:
- `export_overlays.py` (no ProRes alpha needed)
- `capcut_draft_builder.py`
- `validate_capcut_draft.py`
- `package_for_capcut.py`

Bugs that disappear (CapCut-side issues, see [known-bugs.md](./references/known-bugs.md)):
- HEVC keyframe slop (Remotion handles seek correctly)
- Premultiply alpha mismatch (no ProRes export)
- BT.601 vs BT.709 (no ProRes metadata)
- V2 single-track overlay rejection (Remotion has unlimited z-stacking)
- `material_cache` dedup workaround
- CapCut "Link media" reconnection step

Bugs that remain (Remotion constraints):
- Composition IDs cannot contain underscores
- Webpack ignores symlinks (always `cp` the edit_plan.json)
- Sub-pixel aliasing on SVG (`--scale=2` mitigation)

Inherits from `/video-editor`: Remotion components, visual review loop, PNG-first icon rule, overlay density rules, audio-reactive viz, data-driven generation, 3D/Lottie/Rive, etc.

## Working with phases individually

```bash
# Resume after human gate (re-render final after approving proxy):
python build_pipeline.py --input ... --skip-setup --skip-transcribe \
  --skip-filter --skip-plan --skip-assets --skip-remotion --skip-preview

# Just re-render final.mp4 (after editing edit_plan.json):
python ~/.claude/skills/video-editor-remotion/scripts/final_render.py \
  --remotion-dir <output>/remotion \
  --out <output>/final.mp4 \
  --codec h264 --crf 18
```

## Autonomous mode (batch / no human gate)

For batch use cases where you trust the plan + visual review:

```bash
python build_pipeline.py --input ... --autonomous
```

Skips phase 8 (human gate). Visual review loop still runs.

Most useful with `batch_data_driven.py` (CSV → N reels):

```bash
python ~/.claude/skills/video-editor-remotion/scripts/batch_data_driven.py \
  --data aeronaves.csv \
  --remotion-dir <output>/remotion \
  --out-dir <output>/batch/ \
  --concurrency 2
```

## Codec presets

```bash
# Default — H.264, max compatibility
final_render.py --codec h264 --crf 18

# Smaller file (Instagram strips quality anyway)
final_render.py --codec h264 --crf 22

# H.265 (smaller files, slower encode, less universal)
final_render.py --codec h265 --crf 24

# ProRes master (huge files, edit-friendly downstream)
final_render.py --codec prores --pixel-format yuv422p10le

# VP9 (YouTube-native, smaller than H.264 at same quality)
final_render.py --codec vp9 --crf 30
```

See [final-render.md](./references/final-render.md) for full options + concurrency.

## Available Remotion components

(Same library as `/video-editor` sibling — full list in [component-library.md](./references/component-library.md))

Established: `KineticCaption`, `StatOverlay`, `StatChart`, `CounterNumber`, `CinematicTitle`, `LogoBug`, `CodeDocument`, `SplitComparison`, `MismatchCards`, `STFStamp`, `ScaleOfJustice`, etc.

Remotion-package-backed: `TransitionScene`, `AudioWaveform`, `LottieScene`, `RiveScene`, `ThreeReveal`, `MotionBlurOverlay`, `NoiseBackground`, `ShapeMorph`.

## References

- [workflow.md](./references/workflow.md) — pipeline phase-by-phase (Remotion-only)
- [known-bugs.md](./references/known-bugs.md) — Remotion-relevant bugs only
- [final-render.md](./references/final-render.md) — codec/CRF/concurrency reference
- [edit-plan-schema.md](./references/edit-plan-schema.md) — `edit_plan.json` schema
- [remotion-cookbook.md](./references/remotion-cookbook.md) — Remotion recipes
- [remotion-feature-catalog.md](./references/remotion-feature-catalog.md) — full Remotion primitives map
- [component-library.md](./references/component-library.md) — props per component
- [sfx-catalog.md](./references/sfx-catalog.md) — 26 SFX categories
- [overlay-density.md](./references/overlay-density.md) — minimum counts + PNG-first
- [visual-review.md](./references/visual-review.md) — iterative review loop
- [icon-resources.md](./references/icon-resources.md) — PNG bank + Wikimedia
- [aspect-ratios.md](./references/aspect-ratios.md) — 9:16 vs 16:9
- [data-driven-videos.md](./references/data-driven-videos.md) — CSV/JSON → N reels
- [audio-reactive.md](./references/audio-reactive.md) — `useAudioData`
- [3d-and-lottie.md](./references/3d-and-lottie.md) — Three.js + Lottie + Rive
- [preview-player.md](./references/preview-player.md) — embeddable `@remotion/player`
- [best-practices-notebooklm.md](./references/best-practices-notebooklm.md)
- [inspiration-prompts.md](./references/inspiration-prompts.md)

## SFX library quick map

Same library as parent skill: 26 categories at `/Users/gabriel/Documents/EFEITOS SONOROS/`, indexed in `assets/sfx_index.json`. **Use legacy UPPERCASE names in `edit_plan.json`**: `WOOSH`, `CLICK`, `DIGITAL`, `TRANSIÇÃO`, `CAMERA`, `PLIM`, `RISER`, `VARIAVEIS`, `AMBIENTE`, `CINEMATICA`, `ROLAGEM`, `GLITCH`, `TECLADO`, `DINHEIRO`, `ESTALO`, `CONTAGEM`, `POPS`, `BOOM`, `NOTIFICATION`, `DRUM`, `GLASS_BREAK`, `APPLAUSE`, `HORROR`, `FAIL`, `MAGIC`, `HEARTBEAT`.

In this fork, SFX play via `<Audio>` tracks inside `Reel.tsx` — described above in [SFX in Remotion](#sfx-in-remotion-key-difference-from-capcut-sibling).
