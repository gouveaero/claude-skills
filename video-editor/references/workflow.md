# Workflow Detalhado — video-editor pipeline

## Visão geral

```
brutos/ + roteiro.md
        ↓
[1] setup_project.py    → clips_proxy/ (H.264 1080p)
[2] transcribe.py       → transcripts.json (word-level)
[3] filter_raws.py      → clips_selecionados.json + selected/
[4] plan_edit.py        → edit_plan.json (source-of-truth)
[5] request_assets.py   → assets_needed.json (gate se faltar)
[6] build_remotion.py   → remotion/ (projeto Node)
[7] preview.py          → Studio + proxy.mp4
[8] GATE HUMANO         ← você aprova aqui
[9] export_clips.py     → capcut_ready/clips/
[10] export_overlays.py → capcut_ready/overlays/ (.mov alpha)
[11] capcut_draft_builder.py → draft CapCut Desktop
```

## Fase 1 — Setup (`setup_project.py`)

- Detecta `.video-editor.json` subindo na árvore de diretórios
- Transcode de HEVC/10-bit/4K → H.264 yuv420p 1080p via ffmpeg (cached por mtime)
- Cria estrutura `output/<reel-name>/clips_proxy/`
- `--skip-setup` pula se proxies já existirem

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

- **Modo agent (sem API, `--agent`):**
  - Escreve `filter_brief.md` com lista de clips e transcripts
  - Exit code 2 → Claude Code lê o brief e preenche `clips_selecionados.json`

- **Threshold:** `--min-score 0.5` (padrão). Clips abaixo ficam em `rejected[]`.

## Fase 4 — Plan edit (`plan_edit.py`)

Claude (API ou agent) gera `edit_plan.json` com:
- `v1_main[]`: sequência de cuts com `clip`, `source_in`, `source_out`, `slug`
- `subtitle_track[]`: legendas word-level sincronizadas
- `overlays_v2[]`: motion-graphics com `component`, `start_frame`, `end_frame`, `props`
- `transitions[]`: tipo de transição entre cuts
- `sfx[]`: efeitos sonoros por categoria + timestamp
- `zoom_keyframes[]`: keyframes de escala + posição por clip
- `assets_needed[]`: logos/imagens necessários
- `aspect`: "9:16" ou "16:9"
- `color_correction`: grade de cor base

Contexto injetado no system prompt:
- `best-practices-notebooklm.md` (via cache ephemeral)
- Resumo das categorias SFX disponíveis
- Schema de todos os campos obrigatórios

## Fase 5 — Request assets (`request_assets.py`)

- Lê `edit_plan["assets_needed"]`
- Verifica presença em `<input>/assets/`
- Se faltar: escreve `assets_needed.json`, exit 2
- Claude Code lê o manifest, pede ao usuário ou aciona `imagens-freepik`
- Retomar: `build_pipeline.py --skip-setup ... --skip-plan` (pulando tudo até fase 5)

## Fase 6 — Build Remotion (`build_remotion.py`)

- Copia templates (`Root.tsx.tmpl`, `Reel.tsx.tmpl`, `components/`)
- Substitui placeholders (`{{FPS}}`, `{{WIDTH}}`, `{{HEIGHT}}`, etc.)
- Instala dependências Node (`npm install`)
- Injeta `edit_plan.json` como `src/edit_plan.json`
- **Gera Compositions isoladas** para cada overlay em `overlays_v2` com `component` definido (para export alpha individual na fase 10)

## Fase 7 — Preview

`preview.py`:
- Detecta porta livre a partir de 3001
- Lança `npx remotion studio` (hot-reload nativo)
- Abre browser automaticamente
- Em paralelo: `render_proxy.py` gera `proxy.mp4` (540×960, crf 28, escala 0.5×)
- Hot-reload: editar `edit_plan.json` recompila em 1-2s no Studio

## Fase 8 — GATE HUMANO

Após revisar `proxy.mp4` e aprovar no Studio:
```bash
python build_pipeline.py --input ... \
  --skip-setup --skip-transcribe --skip-filter \
  --skip-plan --skip-assets --skip-remotion --skip-preview
```

## Fase 9 — Export clips (`export_clips.py`)

- Para cada cut em `v1_main`: `ffmpeg -ss <source_in> -to <source_out> -c copy`
- Salva como `01_<slug>.mp4`, `02_<slug>.mp4`, ... em `capcut_ready/clips/`
- Usa os **brutos originais** (não os proxies) para qualidade máxima
- Fallback re-encode se stream copy falhar

## Fase 10 — Export overlays (`export_overlays.py`)

- Lê Root.tsx procurando `id="overlay_*"`
- Para cada Composition: `npx remotion render <id> --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png`
- Salva `.mov` em `capcut_ready/overlays/`
- Canal alpha limpo para composição no CapCut

## Fase 11 — Build CapCut draft (`capcut_draft_builder.py`)

Cria draft nativo CapCut Desktop com 4 tracks:
- **Track V1 (vídeo principal):** clips em ordem com transições
- **Track V2 (overlays alpha):** .mov ProRes 4444 com transparência
- **Track A2 (SFX):** efeitos sonoros da biblioteca curada
- **Track T1 (texto):** legendas e textos extras

Zoom keyframes aplicados como keyframes nativos CapCut (propriedades `KFTypeScaleX/Y`, `KFTypePositionX/Y`).

Registra o draft em `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/` para aparecer automaticamente no CapCut Desktop.

## Iteração

O `edit_plan.json` é o ponto de iteração central:
- Edite manualmente ou peça ao Claude para ajustar seções específicas
- Rerun a partir da fase 6 (build_remotion) para ver mudanças no Studio
- Sem re-transcribe, sem re-filter, sem re-plan

## Renderização final HQ (opcional)

```bash
python ~/.claude/skills/video-editor/scripts/render.py \
  --remotion-dir output/reel-01/remotion/ \
  --output output/reel-01/final.mp4
```

Ou diretamente:
```bash
cd output/reel-01/remotion && npx remotion render Reel ../final.mp4
```
