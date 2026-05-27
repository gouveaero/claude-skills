---
name: video-editor
description: >
  Use when the user mentions raw footage, video editing, clips, scripts, cuts, SFX, zooms,
  motion graphics, CapCut drafts, Remotion animations, kinetic captions, reels, TikTok,
  Shorts, YouTube videos, Lottie/Rive/3D scenes for video, audio-reactive visuals,
  data-driven video generation, or thumbnail rendering. Triggers in English and
  Portuguese ("edita esse vídeo", "monta o reel", "gera a timeline", "corta esses clipes",
  "legenda dinâmica", "vídeo curto pra Instagram"). For DaVinci Resolve workflows
  use video-editor-davinci instead.
---

# video-editor

Programmatic video pipeline: Remotion (motion graphics) + CapCut (final NLE deliverable). Battle-tested for Reels/Shorts/TikTok at 9:16 and YouTube at 16:9. **Invoke this skill any time video is mentioned.**

## When to use this vs `/video-editor-davinci`

```
Reels social, motion-graphics heavy, CapCut deliverable      →  /video-editor
Longer-form, color grading needed, DaVinci Studio project    →  /video-editor-davinci
```

If unsure: this skill. CapCut deliverable is the default.

**RELATED SKILLS:** [[vhoe-roteiro]] (input script for Vhoe reels), [[imagens-freepik]] (PNG generation), [[carousel-generator]] (similar HTML→export paradigm), [[video-editor-davinci]] (sibling for DaVinci).

## Quick start

```bash
# Once per machine — check deps (node, ffmpeg, mlx-whisper, pyJianYingDraft, anthropic):
python ~/.claude/skills/video-editor/scripts/check_setup.py

# Run pipeline (11 phases auto, human gate after preview):
python ~/.claude/skills/video-editor/scripts/build_pipeline.py \
  --input ~/Videos/meu-projeto/brutos/ \
  --aspect 9:16 \
  --target-duration 30
```

Project-specific overrides live in `.video-editor.json` anywhere up the directory tree. See [brand-configs/_example.json](./brand-configs/_example.json).

## On activation, ask the user

1. **What do you have?** (raw clips, script/roteiro, partial project, or just an `edit_plan.json`?)
2. **Aspect ratio?** (9:16 Reels/TikTok/Shorts or 16:9 YouTube)
3. **Target duration?** (seconds)

## Pipeline overview (11 phases)

| # | Phase | What it does |
|---|------|-----------|
| 1 | Setup | Transcode HEVC/4K → H.264 1080p (proxy), scaffold output |
| 2 | Transcribe | mlx-whisper word-level on all clips |
| 3 | Filter raws | Select relevant clips (transcript + visual fallback) |
| 4 | Plan edit | Claude generates `edit_plan.json` (cuts, SFX, zooms, overlays, assets) |
| 5 | Request assets | Verify logos/images — block if missing |
| 6 | Build Remotion | Scaffold Node project with custom components + isolated Compositions |
| 7 | Preview | Remotion Studio (hot-reload) + proxy MP4 in parallel |
| **7.5** | **Visual Review** | Auto-QA: agent reviews extracted frames per `rich_overlay`, fixes `RichOverlays.tsx` BEFORE human sees it (see [visual-review.md](./references/visual-review.md)) |
| **8** | **HUMAN GATE** | Review proxy.mp4 and approve before continuing |
| 9 | Export clips | Trim each cut from raw source (stream copy) — debug only |
| 10 | Export overlays | Render each overlay as `.mov` ProRes 4444 alpha (premultiply + BT.709 applied) |
| **11** | **Package + CapCut draft** | Build self-contained `<input>/capcut_package/` (brutos transcoded HEVC→H.264 all-I-frame, hooks separated, SFX copied, preview render). Build draft with absolute paths. |
| **11.5** | **Validate draft** | Hard-check `draft_info.json` vs `edit_plan.json`. ABORT if mismatched. |

For phase details: [workflow.md](./references/workflow.md).

## Deliverable

```
<input>/capcut_package/
├── 01_brutos_hooks/   ← brutos with opening hooks (renamed)
├── 02_brutos_cenas/   ← main scene brutos (renamed by context)
├── 03_sfx/            ← SFX used (copies of selected files)
├── 04_animacoes/preview_com_overlays.mp4
└── README.md
```

Self-contained — zippable, portable. CapCut "Link media" auto-reconnects if folder moves.

## Red Flags — STOP and reconsider

If you catch yourself doing one of these, STOP:

- **"Skip `validate_capcut_draft.py` — só uma iteração de teste"** → HEVC keyframe slop reappears. Validate is a hard gate, not optional.
- **"Visual review é overkill, vi no proxy.mp4 e tá ok"** → overlays <2s slip past eyeball review. Loop is mandatory until iteration #5 or all PASS.
- **"Renderizar overlay sem premultiply+BT.709 — corro depois"** → colors explode in CapCut, becomes invisible until re-render. Always apply both.
- **"Symlink do edit_plan.json pro remotion/src/"** → webpack ignores symlinks. Use `cp`.
- **"Underscore no ID de Composition Remotion"** → render falha imediato. Use hyphens.
- **"Desenhar SVG na mão pra balança / figura humana / brasão"** → output amador. Always PNG-first (see [overlay-density.md](./references/overlay-density.md)). Hard rule from TriboTax 2026-05-12.
- **"Inventar feature do Remotion"** → consulte [remotion-feature-catalog.md](./references/remotion-feature-catalog.md) primeiro. Se não existe, propor alternativa existente.

## Rationalization table

| Excuse | Reality |
|--------|---------|
| "Vou só rodar render — pulo validate" | `source_in` dessincroniza no CapCut. Validate é gate hard. |
| "Visual review é overkill, eu vejo no proxy.mp4" | Overlays curtos (<2s) passam batido. Iteração obrigatória até PASS. |
| "PNG já tá quase certo, vou desenhar SVG" | Resultado amador. PNG-first é não-negociável. |
| "Posso inventar uma feature Remotion" | Não. Consultar `remotion-feature-catalog.md` primeiro. |
| "1 overlay a cada 20s é suficiente" | Não. Mínimo 1 a cada 8-10s. Reel "vazio" parece amador. |
| "Symlink é mais elegante que cp" | Webpack quebra. Use cp. |

## Output structure

```
<input_dir>/../output/<reel-name>/
├── clips_proxy/                ← proxies H.264 1080p
├── transcripts.json            ← word-level transcripts
├── clips_selecionados.json     ← filter result
├── edit_plan.json              ← SOURCE OF TRUTH (edit to iterate)
├── edit_plan_packaged.json     ← version with capcut_package/ absolute paths
├── sfx_index_packaged.json     ← ad-hoc sfx_index pointing to 03_sfx/
├── assets_needed.json          ← external assets manifest
├── remotion/                   ← full Node project
├── proxy.mp4                   ← low-res preview (540×960)
├── capcut_ready/
│   ├── clips/                  ← trimmed cuts (NOT used by draft)
│   └── overlays/               ← Remotion overlays with alpha (.mov ProRes 4444)
└── final.mp4                   ← optional HQ render
```

Originals stay intact. `capcut_package/` is the deliverable copy.

## Available Remotion components

Ready to use in `edit_plan.json` via `overlays_v2[].component` or `rich_overlays[].kind`.

**Established components** (all in [templates/components/](./templates/components/)):
- Captions/typography: `KineticCaption`, `GlitchText`, `LowerThird`
- Stats: `StatOverlay`, `StatChart`, `StatBarChart`, `StatStackedBar`, `CountUp`, `CounterNumber`
- Brand/logo: `LogoBug`, `StampBrand`, `TributavelStamp`, `STFStamp`
- Scene-decoration: `RomanColumnsBg`, `VespasianBust`, `RomanLatrine`, `YearCaption`
- Cinematic: `CinematicTitle`, `GoldCoinDrop`, `WarmShiftPivot`
- Document/legal: `CodeDocument`, `TickerResp`
- Comparison: `SplitComparison`, `MismatchCards`, `MergeIntoKeyword`
- Data viz: `DataNetwork`, `ContextTags`
- Camera moves (snippets): `KenBurns`, `CalloutArrow`, `PiPBroll`
- CTA: `CommentBubbleCta`, `TriboShield`
- Decoration: `RomanScrollWipe`, `ScaleOfJustice`, `HighlighterUnderline`

**New components** (added in this skill upgrade — see [remotion-feature-catalog.md](./references/remotion-feature-catalog.md)):
- `TransitionScene` (uses `@remotion/transitions` — fade/slide/wipe/cube/clock-wipe)
- `AudioWaveform` (uses `@remotion/media-utils` — bars reacting to narration)
- `LottieScene` (uses `@remotion/lottie` — After Effects animations)
- `RiveScene` (uses `@remotion/rive` — vector animations)
- `ThreeReveal` (uses `@remotion/three` — 3D scenes, e.g. aircraft rotation for Vhoe)
- `MotionBlurOverlay` (uses `@remotion/motion-blur` — cinematic trails)
- `NoiseBackground` (uses `@remotion/noise` — procedural grain/perlin)
- `ShapeMorph` (uses `@remotion/shapes` + `@remotion/paths` — geometric morph)

Component props detailed in [component-library.md](./references/component-library.md).

## Working with phases individually

```bash
# Resume after human gate:
python build_pipeline.py --input ... --skip-setup --skip-transcribe \
  --skip-filter --skip-plan --skip-assets --skip-remotion --skip-preview

# Only regenerate CapCut draft (after editing edit_plan.json):
python build_pipeline.py --input ... --skip-setup --skip-transcribe \
  --skip-filter --skip-plan --skip-assets --skip-remotion --skip-preview \
  --skip-export --skip-overlays
```

## What's new — Remotion features added

This skill now uses ~40 Remotion primitives and packages (vs ~15 before). Key additions documented in references:

- **Type-safe data-driven videos**: Zod schemas + `calculateMetadata` → generate N reels from CSV/JSON (e.g., 50 Vhoe reels from `aeronaves.csv`). See [data-driven-videos.md](./references/data-driven-videos.md).
- **Audio-reactive visuals**: `useAudioData` / `visualizeAudio` from `@remotion/media-utils` driving overlay animations. See [audio-reactive.md](./references/audio-reactive.md).
- **3D + Lottie + Rive**: `@remotion/three`, `@remotion/lottie`, `@remotion/rive` for aircraft reveals, animated logos, vector scenes. See [3d-and-lottie.md](./references/3d-and-lottie.md).
- **Embeddable preview**: `@remotion/player` for client approval URLs before final render. See [preview-player.md](./references/preview-player.md).
- **Auto thumbnails**: `<Still>` Composition + `renderStill()` for Instagram/YouTube cover frames.
- **Google Fonts**: `@remotion/google-fonts` (no network delay at render).
- **Optional Tailwind v4**: `@remotion/tailwind-v4` via `--with-tailwind` flag in `build_remotion.py`.

Full catalog: [remotion-feature-catalog.md](./references/remotion-feature-catalog.md).

## References

- [workflow.md](./references/workflow.md) — pipeline phase-by-phase
- [known-bugs.md](./references/known-bugs.md) — bug catalog with fixes (HEVC slop, alpha straight, BT.601 mismatch, etc.)
- [edit-plan-schema.md](./references/edit-plan-schema.md) — `edit_plan.json` schema
- [remotion-cookbook.md](./references/remotion-cookbook.md) — Remotion recipes (springs, sequences, transitions)
- [remotion-feature-catalog.md](./references/remotion-feature-catalog.md) — every Remotion primitive/package mapped
- [component-library.md](./references/component-library.md) — props per component
- [capcut-draft-schema.md](./references/capcut-draft-schema.md) — CapCut draft JSON schema
- [sfx-catalog.md](./references/sfx-catalog.md) — 26 SFX categories, usage rules
- [overlay-density.md](./references/overlay-density.md) — minimum overlay counts + PNG-first rule
- [visual-review.md](./references/visual-review.md) — iterative review loop
- [icon-resources.md](./references/icon-resources.md) — PNG bank + Wikimedia workflow
- [aspect-ratios.md](./references/aspect-ratios.md) — 9:16 vs 16:9 rules
- [data-driven-videos.md](./references/data-driven-videos.md) — CSV/JSON → N reels
- [audio-reactive.md](./references/audio-reactive.md) — `useAudioData` recipes
- [3d-and-lottie.md](./references/3d-and-lottie.md) — Three.js + Lottie + Rive
- [preview-player.md](./references/preview-player.md) — embeddable `@remotion/player`
- [best-practices-notebooklm.md](./references/best-practices-notebooklm.md) — editing principles from Gabriel's NotebookLM
- [inspiration-prompts.md](./references/inspiration-prompts.md) — Remotion animation prompt digest

## SFX library quick map

26 categories at `/Users/gabriel/Documents/EFEITOS SONOROS/`, indexed in `assets/sfx_index.json`. **Use legacy UPPERCASE names in `edit_plan.json`**: `WOOSH`, `CLICK`, `DIGITAL`, `TRANSIÇÃO`, `CAMERA`, `PLIM`, `RISER`, `VARIAVEIS`, `AMBIENTE`, `CINEMATICA`, `ROLAGEM`, `GLITCH`, `TECLADO`, `DINHEIRO`, `ESTALO`, `CONTAGEM`, `POPS`, `BOOM`, `NOTIFICATION`, `DRUM`, `GLASS_BREAK`, `APPLAUSE`, `HORROR`, `FAIL`, `MAGIC`, `HEARTBEAT`.

Typical volume: -6 to -12 dB (SFX) vs 0 dB (voice). Full usage rules in [sfx-catalog.md](./references/sfx-catalog.md).

Regenerate index after adding/removing files:

```bash
python ~/.claude/skills/video-editor/scripts/regenerate_sfx_index.py
```
