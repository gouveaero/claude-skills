# Known Bugs & Countermeasures (Remotion-only fork)

Bugs that apply to this fork. CapCut-side bugs from the parent skill are removed —
this pipeline renders the final MP4 inside Remotion, so the entire CapCut decoder
surface disappears.

## Bugs that DO apply (Remotion-side)

### IDs Remotion com underscore quebram

**Sintoma:** `Error: Composition id can only contain a-z, A-Z, 0-9, CJK characters and -`.

**Fix:** sempre usar hifens (`overlay-00-stamp-brand`), nunca underscores.

---

### Symlink do edit_plan.json não funciona no Remotion (webpack)

**Sintoma:** `Error: Module not found: Error: Can't resolve './edit_plan.json'` ao rodar `npx remotion render`, mesmo o symlink parecendo válido no terminal.

**Causa:** o webpack 5 (usado pelo Remotion) não segue symlinks por padrão. `ln -sf ../edit_plan.json remotion/src/edit_plan.json` cria um link válido no filesystem mas o bundler falha ao resolver o módulo.

**Fix:** sempre usar `cp` para sincronizar o `edit_plan.json`:

```bash
cp <output>/edit_plan_resolved.json <remotion-dir>/src/edit_plan.json
```

Após cada edição no `edit_plan.json` raiz, rodar o `cp` antes de re-renderizar. **Não usar symlinks** — eles funcionam pra leitura manual mas quebram o bundler.

---

### Overlays Remotion com bordas serrilhadas (sub-pixel aliasing)

**Sintoma:** SVG paths, textos com peso baixo e ícones com transparência aparecem com bordas serrilhadas no MP4 final. Aliasing perceptível especialmente em diagonais e curvas finas.

**Causa:** Chrome headless rasteriza o overlay em 1080×1920 = 1× a resolução final. SVG paths sub-pixel ficam aliased porque o rasterizer não tem buffer para supersampling.

**Fix:** rodar `npx remotion render --scale=2` — Chrome rasteriza em 2160×3840 e downscale pra 1080×1920 dá supersampling 2×2. Bordas SVG ficam visivelmente mais suaves. Custo: ~3× o tempo de render, ~2× o tamanho dos PNG intermediários.

`final_render.py --scale 2` aplica isso automaticamente.

**Para casos onde 2× ainda não basta** (logos finos, texto pequeno): `--scale=4` ou aumente o `width/height` da Composition pra 2× e baixe o `transform: scale(0.5)` no root.

---

### Arquivos transcodados corrompidos por interrupção

**Sintoma:** `Invalid NAL unit` / `Error splitting the input into NAL units` ao tentar usar um proxy transcodado pelo `setup.py`.

**Causa:** transcode interrompido no meio (ctrl-c, kill -9, OOM) deixando o MP4 com header válido mas streams truncados.

**Fix:** sempre verificar integridade após encode decodificando ~1s de frames. Se erro, deletar e re-encodar. Implementado em `transcode_to_h264_all_keyframe()`.

---

### SFX com volume diferente do esperado

**Sintoma:** SFX toca muito alto ou muito baixo comparado ao plan. Volume não bate com `volume_db` declarado.

**Causa:** confusão entre dB e ganho linear. `volume_db: -10` significa "10 dB abaixo do pico", que em linear é ~0.316. `<Audio volume={0.316}>` aplica ganho linear, e Remotion mixa sem auto-clipping.

**Fix:** `Reel.tsx` usa `volume={Math.pow(10, volume_db / 20)}` — converte dB pra ganho linear conforme spec acústica. Vale conferir num spectrum analyzer (`ffprobe -show_entries frame=...` ou Audacity) se algum SFX parecer fora de proporção.

---

### Múltiplos `<Audio>` simultâneos clipam

**Sintoma:** quando 3+ SFX tocam ao mesmo tempo (ex: WOOSH + PLIM + voz), o áudio final estoura/distorce nos picos.

**Causa:** Remotion soma os ganhos lineares de cada faixa sem auto-ducking. 3 faixas em -10dB cada somam para mais de -5dB perceptual; voz a 0dB + SFX a -10dB clipa nos transientes.

**Fix:** mantém SFX em -12dB a -15dB quando houver overlap esperado. Ou rode `final_render.py --audio-codec aac --audio-bitrate 192k` que aplica soft-clip implícito do AAC encoder. Casos extremos: pre-mix com ffmpeg `loudnorm` antes do render final.

---

### `<OffthreadVideo>` sem áudio

**Sintoma:** o áudio do bruto (voz) não toca no Reel mesmo o vídeo aparecendo bem.

**Causa:** `<OffthreadVideo>` por padrão inclui áudio mas requer `volume` callback ou prop explícito pra ser auditivo no render final.

**Fix:** já tratado em `VideoCut.tsx` (volume callback com fade in/out). Se criar componente custom de vídeo, lembre de passar `volume`.

---

### `<Audio>` em loop infinito sem `endAt`

**Sintoma:** SFX longo (RISER 19s) declarado em `edit_plan.sfx[]` em t=0ms continua tocando até o final do reel, atropelando outros.

**Causa:** sem `endAt` ou `<Sequence durationInFrames>`, o `<Audio>` toca a faixa inteira a partir de `startFrom`.

**Fix:** `Reel.tsx` envolve cada SFX em `<Sequence>` com `durationInFrames` baseado no `SFX_DURATION_CAPS_MS` por categoria. Se a categoria não tem cap, usa a duração do arquivo (clamped at 5s) ou o tempo até o próximo SFX (-50ms folga).

---

### `<Audio>` carrega mas não toca no preview do Studio

**Sintoma:** Remotion Studio mostra a waveform mas o áudio não sai dos alto-falantes.

**Causa:** browser autoplay policy — o áudio não toca até o usuário clicar no preview pelo menos uma vez.

**Fix:** clique no preview pra liberar. Esse comportamento é só no Studio; no render final via `npx remotion render` o áudio é embutido normalmente.

---

## Bugs que DESAPARECEM neste fork

Os bugs abaixo existiam no `/video-editor` pai (com deliverable CapCut). Aqui não se aplicam mais — documentados pra contexto:

| Bug pai | Por que não se aplica |
|---|---|
| HEVC keyframe slop | Remotion seek é frame-accurate via ffmpeg `-ss` |
| Overlay premultiply (luz estourada) | Não há export ProRes alpha — Remotion compõe direto |
| BT.601 vs BT.709 mismatch | Idem — H.264/H.265 são re-encodados com primaries corretas |
| V2 single-track rejection | Remotion tem z-stacking ilimitado de `<Sequence>` |
| material_cache dedup | Não há draft JSON — `<OffthreadVideo>` lida com clips independentemente |
| CapCut "Link media" reconnection | Não há draft — `final.mp4` é self-contained |
| `package_for_capcut.py` KeyError | Script removido neste fork |
| HEVC all-I-frame transcode requirement | Não precisa — Remotion seek funciona com HEVC keyframe longo |
| V2 overlays vazios (no isolated Composition) | Não precisa — overlays renderizam no Reel.tsx direto, sem export isolado |

## Adicionando novos bugs

Quando descobrir um bug novo:
1. Reproduz em um projeto de teste mínimo
2. Documenta sintoma + causa + fix aqui
3. Se for um padrão de rationalização (agent escolhe atalho errado), adiciona em SKILL.md's Red Flags + rationalization table
4. Se for mecânico (catch automático), adiciona check em `check_setup.py` ou `final_render.py`
