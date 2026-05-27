# Workflow Detalhado — video-editor-remotion pipeline

100% Remotion. Sem CapCut, sem ProRes alpha export, sem package autocontido.
Deliverable: um único `final.mp4`.

## Visão geral

```
brutos/ + roteiro.md
        ↓
[1] setup_project.py    → clips_proxy/ (H.264 1080p)
[2] transcribe.py       → transcripts.json (word-level)
[3] filter_raws.py      → clips_selecionados.json + selected/
[4] plan_edit.py        → edit_plan.json (source-of-truth)
[5] request_assets.py   → assets_needed.json (gate se faltar)
[6] build_remotion.py   → remotion/ + SFX em public/sfx/ + edit_plan_resolved.json
[7] preview.py          → Studio + proxy.mp4
[7.5] visual_review.py  → frames extraídos + brief de auto-QA
[8] GATE HUMANO         ← você aprova aqui (pulado com --autonomous)
[9] final_render.py     → final.mp4 (1080×1920 H.264 CRF 18)
[9.5] render_thumbnail.py → thumbnail.png (opcional)
```

## Fase 1 — Setup (`setup_project.py`)

- Detecta `.video-editor.json` subindo na árvore de diretórios
- Transcode de HEVC/10-bit/4K → H.264 yuv420p 1080p via ffmpeg (cached por mtime)
- Cria estrutura `output/<reel-name>/clips_proxy/`
- `--skip-setup` pula se proxies já existirem
- **Diferença vs skill pai:** não precisa de all-I-frame H.264 — Remotion seek é frame-accurate independente do GOP

## Fase 2 — Transcribe (`transcribe.py`)

- mlx-whisper com `--word-timestamps` em cada proxy
- Salva `transcripts.json`: `{filename: {text, words: [{word, start, end}]}}`
- Cached por hash do arquivo (não re-transcreve se não mudou)

## Fase 3 — Filter raws (`filter_raws.py`)

- **Modo padrão (com API):**
  1. Lê transcripts + roteiro → Claude API com prompt caching
  2. Para clips com `needs_visual_check=true` (b-roll/silêncio): extrai 3 frames via ffmpeg e faz passagem multimodal
  3. Gera `clips_selecionados.json` com `{clip, score, motivo, needs_visual_check}`
  4. Cria `selected/` com symlinks para os clips aprovados (brutos intactos)
- **Modo agent (sem API, `--agent`):** escreve `filter_brief.md`, exit code 2 → Claude Code preenche o JSON

## Fase 4 — Plan edit (`plan_edit.py`)

Claude (API ou agent) gera `edit_plan.json` com:
- `v1_main[]`: sequência de cuts com `clip`, `source_in`, `source_out`, `slug`/`rationale`
- `subtitle_track[]`: legendas word-level sincronizadas
- `overlays_v2[]`: motion-graphics com `component`, `start_frame`, `end_frame`, `props`
- `transitions[]`: tipo de transição entre cuts
- `sfx[]`: efeitos sonoros por categoria + timestamp (resolvidos pra arquivos na fase 6)
- `music[]` (opcional): tracks de música de fundo
- `rich_overlays[]`: overlays director-level (StampBrand, ScaleOfJustice, etc.)
- `assets_needed[]`: logos/imagens necessários
- `aspect`: "9:16" ou "16:9"
- `color_correction`: grade de cor base via CSS filter

Contexto injetado: `best-practices-notebooklm.md`, resumo das categorias SFX, schema dos campos.

## Fase 5 — Request assets (`request_assets.py`)

- Lê `edit_plan["assets_needed"]`
- Verifica presença em `<input>/assets/`
- Se faltar: escreve `assets_needed.json`, exit 2
- Claude Code lê o manifest, pede ao usuário ou aciona `imagens-freepik`
- Retomar: `build_pipeline.py --skip-setup ... --skip-plan` (pulando tudo até fase 5)

## Fase 6 — Build Remotion (`build_remotion.py`)

Diferença chave vs skill pai: **resolve e copia SFX para `public/sfx/`** antes de gravar o `edit_plan.json` interno.

1. Copia templates (`Root.tsx.tmpl`, `Reel.tsx.tmpl`, `ReelThumbnail.tsx.tmpl`, `components/`)
2. Substitui placeholders (`{{FPS}}`, `{{WIDTH}}`, `{{HEIGHT}}`, `{{DURATION_MS_DEFAULT}}`)
3. **Resolve SFX**: para cada `plan.sfx[]`, escolhe arquivo via `sfx_index.json` + seed determinístico, copia para `public/sfx/<filename>`, e injeta `file` + `duration_cap_ms` no entry
4. Escreve `edit_plan_resolved.json` no output dir (snapshot do plan com SFX resolvidos)
5. Escreve `<remotion>/src/edit_plan.json` com plan resolvido
6. Instala dependências Node (`npm install` — pacotes condicionais conforme overlays usados)
7. Copia logo da brand config para `public/`

## Fase 7 — Preview

`preview.py`:
- Detecta porta livre a partir de 3001
- Lança `npx remotion studio` (hot-reload nativo)
- Em paralelo: `render_proxy.py` gera `proxy.mp4` (540×960, crf 28, escala 0.5×)
- Hot-reload: editar `edit_plan.json` recompila em 1-2s no Studio

## Fase 7.5 — Visual Review (`visual_review.py`)

Auto-QA antes do gate humano:
1. Extrai 1 frame por `rich_overlay` do proxy
2. Escreve `visual_review_brief.md` com checklist por kind
3. Agent revisa frames + brief, conserta `RichOverlays.tsx`, re-renderiza
4. Loop até PASS ou iteração #5

## Fase 8 — GATE HUMANO

Após revisar `proxy.mp4` e aprovar:
```bash
python build_pipeline.py --input ... \
  --skip-setup --skip-transcribe --skip-filter \
  --skip-plan --skip-assets --skip-remotion --skip-preview
```

Pulável com `--autonomous` se você confia na visual review automática.

## Fase 9 — Final render (`final_render.py`)

Diferença chave vs skill pai: **um único MP4, não draft CapCut**.

```bash
final_render.py \
  --remotion-dir <output>/remotion \
  --out <output>/final.mp4 \
  --codec h264 --crf 18 \
  --scale 2  # opcional, supersample SVG
```

Internamente chama `npx remotion render Reel <out> --codec h264 --crf 18 --enforce-audio-track --audio-codec aac --audio-bitrate 192k`.

Tempo típico: 1-3 min por minuto de reel @ M2. Ver [final-render.md](./final-render.md) para tuning de concurrency, CRF, codec presets.

## Fase 9.5 — Thumbnail (opcional)

```bash
render_thumbnail.py \
  --remotion-dir <output>/remotion \
  --out <output>/thumbnail.png \
  --frame-ms 80000 \
  --title "TÍTULO DA CAPA"
```

Ou via `--thumbnail-frame-ms` no `build_pipeline.py`.

## Iteração

O `edit_plan.json` é o ponto de iteração central:
- Edite manualmente ou peça ao Claude para ajustar seções específicas
- Rerun a partir da fase 6 (build_remotion) para re-resolver SFX e ver mudanças no Studio
- Para só re-renderizar o final.mp4 após editar o plan:
  ```bash
  cp <output>/edit_plan.json <output>/remotion/src/edit_plan.json
  python3 final_render.py --remotion-dir <output>/remotion --out <output>/final.mp4
  ```

## Batch (CSV → N reels)

Útil quando você tem N variações da mesma estrutura (50 reels Vhoe, um por aeronave):

```bash
python ~/.claude/skills/video-editor-remotion/scripts/batch_data_driven.py \
  --data aeronaves.csv \
  --remotion-dir <output>/remotion \
  --out-dir <output>/batch/ \
  --concurrency 2
```

Ver [data-driven-videos.md](./data-driven-videos.md).
