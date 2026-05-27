# Known Bugs & Countermeasures

Hard-won fixes from real iterations. **Keep these countermeasures present in the workflow** — they catch silent failures that bypass eyeball review.

## V1 cuts mostrando trecho errado / fora de ordem

**Sintoma:** alguns cuts aparecem mostrando o mesmo trecho de outro cut do mesmo bruto. `source_in` fica zerado pra cuts intermediários.

**Causa:** `capcut_draft_builder` criava uma `VideoMaterial` distinta por `VideoSegment`. Quando CapCut abre o draft, dedupa silenciosamente por path e zera `source_timerange.start` de segments que apontavam pra "mesma" material — só o primeiro/último é preservado, os outros viram `src=0`.

**Fix:** `material_cache` por path em `build_draft()` — uma `VideoMaterial` por arquivo, vários `VideoSegment` reusando a mesma material. `validate_capcut_draft.py` detecta com erro hard "source_in esperado X, draft tem Y".

---

## SFX em looping / overlap caótico

**Sintoma:** mesmo SFX toca repetido, sons longos (riser 19s) atropelam outros, áudio fica fora de contexto.

**Causa:** `target_timerange.duration` era setado igual à duração TOTAL do arquivo. Riser de 19s @ 0ms tocava até 19s, sobrepondo o WOOSH @ 8.5s.

**Fix:** `SFX_DURATION_CAPS_MS` por categoria em `capcut_draft_builder` + trim até o próximo SFX (-50ms folga). Validador alerta se algum SFX passar do cap.

---

## V2 overlays vazios

**Sintoma:** `rich_overlays` renderizam no proxy mas no CapCut só aparecem cuts + captions, sem motion graphics.

**Causa:** fase 10 (`export_overlays.py`) era pulada porque `Reel.tsx` era monolítica — sem `Composition` isolada por overlay com fundo transparente.

**Fix:** `Root.tsx` registra uma `Composition` por `rich_overlay` usando `OverlayClip.tsx` (fundo `transparent`). Id no formato `overlay-{idx:02d}-{kind}` (Remotion proíbe underscore). `export_overlays.py` renderiza cada uma como `.mov` ProRes 4444 alpha; builder coloca em V2+ com `timeline_start` do plan.

---

## Vídeo dessincronizado do áudio/captions no CapCut (HEVC keyframe slop)

**Sintoma:** áudio + captions tocam em sync, mas o vídeo aparece atrasado — speaker fala "X" mas vídeo mostra cena de "Y" segundos antes. Mais perceptível quando `source_in` cai entre keyframes.

**Causa:** brutos da câmera vêm em HEVC com keyframe a cada ~1.1s. Quando CapCut faz seek pra `source_in=1.04s`, ele decodifica desde o keyframe anterior (0s) e exibe a partir desse keyframe (sem fast-forward até o source_in pedido). Áudio é PCM/AAC frame-accurate, então corta certo. Resultado: até ~1s de drift entre vídeo e áudio.

**Por que o proxy.mp4 (Remotion) não tem esse bug:** Remotion usa ffmpeg com `-ss source_in -i bruto` que reposiciona corretamente. CapCut tem seu próprio decoder que ignora `source_timerange.start` em HEVC com GOP longo.

**Fix:** transcodar brutos pra H.264 com `-g 1 -keyint_min 1 -sc_threshold 0` (all I-frame = todo frame é keyframe → seek 100% frame-accurate). Custo: arquivos ~4× maiores mas seek perfeito.

```bash
ffmpeg -i bruto.mp4 -c:v libx264 -preset slow -crf 18 \
  -g 1 -keyint_min 1 -sc_threshold 0 \
  -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart \
  bruto_h264_allI.mp4
```

**Fluxo na skill:** integrado em `package_for_capcut.py` antes de copiar pra `capcut_package/`. Sem isso o CapCut nunca vai exibir o `source_in` word-precise.

---

## Overlays com "luz estourada" — alpha straight tratada como premultiplied (CRÍTICO)

**Sintoma:** cards/badges com fundo translúcido aparecem com cor cheia/glow no CapCut, como se houvesse uma luz forte. Áreas que deveriam ser sutilmente tingidas viram blocos vibrantes. Mais perceptível em `split_comparison`, `stamp_brand`, qualquer overlay com `bg-color + alpha < 100%`.

**Causa:** Remotion render produz PNG com **straight alpha** (padrão Chrome rasterizer). Apple ProRes 4444 spec define alpha como **premultiplied**. CapCut/Premiere/AE seguem a spec → tratam o overlay como premultiplied. Quando RGB straight é interpretado como premultiplied, a fórmula de composite vira `result = pixel.RGB + bg * (1-alpha)` em vez de `result = pixel.RGB * alpha + bg * (1-alpha)` — RGB aparece em força total mesmo onde alpha < 100%.

**Como detectar:** abra um frame do `.mov` com PIL: pixels com `alpha=37/255` (14%) tendo `RGB=(248, 241, 234)` (cor cheia) = straight; deveria ser `RGB=(36, 35, 34)` (RGB × alpha) pra ser premultiplied correto.

**Fix:** post-process com ffmpeg `premultiply=inplace=1` filter (re-encode obrigatório):

```bash
ffmpeg -i overlay.mov \
  -vf "premultiply=inplace=1" \
  -c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -bsf:v "prores_metadata=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
  overlay_fixed.mov
```

**Onde aplicar:** `export_overlays.py:_premultiply_and_tag_bt709()` chamado automaticamente após cada `npx remotion render`. Aplica os DOIS fixes (premultiply + BT.709) em uma única passada. Custo: ~10s por overlay (re-encode necessário, mas paralelo via `xargs -P`).

---

## Overlays com cor "puxada" — BT.601 vs BT.709 mismatch

**Sintoma:** cores em geral parecem fora — saturação errada, tons quentes parecem amarelados. Distinto de "luz estourada" — afeta o look geral, não apenas highlights.

**Causa:** ProRes sem metadata `color_primaries`/`color_trc`/`colorspace` → CapCut adivinha BT.601 (SD) num conteúdo HD que foi rasterizado em sRGB/BT.709.

**Fix:** marcar BT.709 explicitamente (incluído no mesmo fix de premultiply acima). Verificar com:

```bash
ffprobe -show_entries stream=color_range,color_space,color_primaries,color_transfer overlay.mov
# deve mostrar: color_space=bt709 color_primaries=bt709 color_transfer=bt709
```

---

## Arquivos transcodados corrompidos por interrupção

**Sintoma:** ao tentar usar um bruto transcodado, `pyJianYingDraft` falha com "没有视频轨道或图片轨道" ou ffmpeg reporta `Invalid NAL unit` / `Error splitting the input into NAL units`.

**Causa:** o transcode foi interrompido no meio (ctrl-c, kill -9, OOM) deixando o MP4 com header válido mas streams truncados.

**Fix:** sempre verificar integridade após encode decodificando ~1s de frames. Se erro, deletar e re-encodar. Implementado em `transcode_to_h264_all_keyframe()` — falha automaticamente em vez de gerar pacote silenciosamente quebrado.

---

## Overlays Remotion com bordas serrilhadas (sub-pixel aliasing)

**Sintoma:** SVG paths, textos com peso baixo e ícones com transparência aparecem com bordas serrilhadas no `.mov` ProRes. Aliasing perceptível especialmente em diagonais e curvas finas.

**Causa:** Chrome headless rasteriza o overlay em 1080×1920 = 1× a resolução final. SVG paths sub-pixel ficam aliased porque o rasterizer não tem buffer para supersampling.

**Fix:** rodar `npx remotion render --scale=2` — Chrome rasteriza em 2160×3840 e downscale pra 1080×1920 dá supersampling 2×2. Bordas SVG ficam visivelmente mais suaves. Custo: ~3× o tempo de render, ~2× o tamanho dos PNG intermediários. ProRes 4444 final tem o mesmo tamanho.

**Para casos onde 2× ainda não basta** (logos finos, texto pequeno): `--scale=4` ou aumente o `width/height` da Composition pra 2× e baixe o `transform: scale(0.5)` no root — efetivamente renderiza em alta res e o ProRes preserva.

---

## V2 single-track rejeita overlays sobrepostos

**Sintoma:** `rich_overlays` como `roman_columns_bg` (14s) coexistindo com `vespasian_bust` (5.6s) e `roman_latrine` (2.6s) — `pyJianYingDraft` rejeita overlap dentro da mesma track com erro `SegmentOverlap`.

**Causa:** uma track de vídeo no CapCut só aceita segmentos sequenciais, não simultâneos. Plan declara overlays simultâneos por design (background + foreground).

**Fix:** [capcut_draft_builder.py:330-365](/Users/gabriel/.claude/skills/video-editor/scripts/capcut_draft_builder.py#L330-L365) — greedy track assignment cria `overlays_alpha_v2`, `overlays_alpha_v3`, `overlays_alpha_v4`... conforme necessário. Cada overlay vai pra primeira track livre no seu range temporal.

**Também:** `script.add_segment(seg, track_name="overlays_alpha_v2")` — quando há múltiplas tracks do mesmo tipo, o nome é obrigatório.

---

## IDs Remotion com underscore quebram

**Sintoma:** `Error: Composition id can only contain a-z, A-Z, 0-9, CJK characters and -`.

**Fix:** sempre usar hifens (`overlay-00-stamp-brand`), nunca underscores.

---

## Symlink do edit_plan.json não funciona no Remotion (webpack)

**Sintoma:** `Error: Module not found: Error: Can't resolve './edit_plan.json'` ao rodar `npx remotion render`, mesmo o symlink parecendo válido no terminal.

**Causa:** o webpack 5 (usado pelo Remotion) não segue symlinks por padrão. `ln -sf ../edit_plan.json remotion/src/edit_plan.json` cria um link válido no filesystem mas o bundler falha ao resolver o módulo.

**Fix:** sempre usar `cp` para sincronizar o `edit_plan.json`:

```bash
cp <output>/edit_plan.json <remotion-dir>/src/edit_plan.json
```

Após cada edição no `edit_plan.json` raiz, rodar o `cp` antes de re-renderizar. **Não usar symlinks** — eles funcionam pra leitura manual mas quebram o bundler.

---

## package_for_capcut.py quebra em plans sem campo `slug`

**Sintoma:** `KeyError: 'slug'` em `derive_bruto_scene_name()` ou `is_hook` ao rodar `package_for_capcut.py`.

**Causa:** script assumia que cada cut em `v1_main` tinha um campo `"slug"`. Plans gerados por Claude usam `"rationale"` em vez de `"slug"`.

**Fix:** `_cut_slug(cut)` com fallback: `cut.get("slug") or slug(cut.get("rationale") or cut.get("clip") or "scene")`. Implementado em 2026-05-13.
