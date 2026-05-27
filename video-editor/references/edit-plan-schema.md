# Schema — edit_plan.json

O `edit_plan.json` é o source-of-truth do pipeline. Tudo o que acontece no Remotion e no CapCut é derivado deste arquivo.

## Estrutura completa

```json
{
  "aspect": "9:16",
  "fps": 30,
  "resolution": [1080, 1920],
  "target_duration_s": 30,
  "color_correction": {
    "contrast": 1.05,
    "saturation": 1.1,
    "brightness": 0.02,
    "color_grade": "warm"
  },
  "v1_main": [
    {
      "clip": "filename.mp4",
      "source_in": 1.5,
      "source_out": 8.2,
      "slug": "abertura-hook",
      "timeline_start": 0
    }
  ],
  "transitions": [
    {
      "after_cut_index": 0,
      "type": "fade",
      "duration_frames": 6
    }
  ],
  "subtitle_track": [
    {
      "start_frame": 0,
      "end_frame": 30,
      "text": "Você sabe quanto está pagando de imposto?",
      "emphasis_words": ["quanto", "imposto"]
    }
  ],
  "overlays_v2": [
    {
      "id": "stat_01",
      "component": "StatOverlay",
      "start_frame": 45,
      "end_frame": 105,
      "filename": "overlay_0_stat_01",
      "props": {
        "value": "30%",
        "label": "de economia possível",
        "accentColor": "#C8A96E"
      }
    },
    {
      "id": "countup_01",
      "component": "snippets/CountUp",
      "start_frame": 120,
      "end_frame": 180,
      "filename": "overlay_1_countup_01",
      "props": {
        "target": 150000,
        "prefix": "R$ ",
        "suffix": " recuperados",
        "accentColor": "#C8A96E"
      }
    }
  ],
  "sfx": [
    {
      "at_ms": 0,
      "category": "RISER",
      "intent": "build-up antes do hook principal",
      "volume_db": -12
    },
    {
      "at_ms": 1500,
      "category": "WOOSH",
      "intent": "transição para o primeiro clip",
      "volume_db": -8
    },
    {
      "at_ms": 4200,
      "category": "PLIM",
      "intent": "destaque do número 30%",
      "volume_db": -10
    },
    {
      "at_ms": 18000,
      "category": "CINEMATICA",
      "intent": "impacto no ponto de virada da narrativa",
      "volume_db": -6
    }
  ],
  "zoom_keyframes": [
    {
      "clip_idx": 0,
      "at_ms": 0,
      "scale": 1.0,
      "transform_x": 0.0,
      "transform_y": 0.0
    },
    {
      "clip_idx": 0,
      "at_ms": 2000,
      "scale": 1.15,
      "transform_x": 0.0,
      "transform_y": -0.05
    },
    {
      "clip_idx": 2,
      "at_ms": 0,
      "scale": 1.0
    },
    {
      "clip_idx": 2,
      "at_ms": 300,
      "scale": 1.2
    }
  ],
  "assets_needed": ["logo.png", "grafico_crescimento.png"],
  "audio_sync_beats": []
}
```

## Campos detalhados

### `aspect`
`"9:16"` — Reels, TikTok, Shorts (1080×1920)
`"16:9"` — YouTube, LinkedIn horizontal (1920×1080)

### `v1_main[]`
Sequência principal de clips. Cada item:
- `clip`: filename relativo à pasta de proxies/selected
- `source_in / source_out`: timestamps em segundos (float)
- `slug`: identificador curto sem espaços (usado como nome de arquivo no export)
- `timeline_start`: início no timeline final (calculado automaticamente pelo orquestrador)

### `transitions[]`
- `type`: `"fade"` | `"slide_up"` | `"slide_down"` | `"wipe"` | `"none"`
- `duration_frames`: duração da transição em frames (padrão 6)
- `after_cut_index`: índice do cut em `v1_main` APÓS o qual a transição ocorre

### `subtitle_track[]`
- `start_frame / end_frame`: frames absolutos no timeline
- `text`: texto completo do segmento
- `emphasis_words`: palavras a receber destaque visual (spring scale-pop no KineticCaption)

### `overlays_v2[]`
- `component`: nome do componente Remotion. Valores válidos:
  - `"KineticCaption"`, `"StatOverlay"`, `"StatChart"`, `"StatBarChart"`, `"CascadeGraphic"`, `"LogoBug"`
  - Snippets: `"snippets/CountUp"`, `"snippets/KenBurns"`, `"snippets/GlitchText"`, `"snippets/CalloutArrow"`, `"snippets/LowerThird"`, `"snippets/PiPBroll"`
- `filename`: id único sem espaços (usado como nome da Composition isolada no Remotion e do .mov exportado)
- `props`: props específicas do componente (ver `references/component-library.md`)

### `sfx[]`
- `at_ms`: millisegundos desde o início do vídeo (não do clip)
- `category`: uma das 17 categorias do `sfx_index.json` (WOOSH, PLIM, RISER, etc.)
- `intent`: por que este SFX aqui (informacional, não afeta o render)
- `volume_db`: nível em dB (valores típicos: -6 a -14)

**Regras de uso recomendadas:**
- RISER: sempre no início (0ms), antes do hook
- WOOSH: em cada corte entre clips (sincronizado com `timeline_start` do cut)
- PLIM: ao destacar números, check-marks, revelações positivas
- CINEMATICA: para o momento de maior impacto (máx 1 por vídeo)
- GLITCH: para pattern interrupts / virada de narrativa
- Mínimo 3 SFX por vídeo de 30s. Máximo 12.

### `zoom_keyframes[]`
- `clip_idx`: índice do clip em `v1_main` (0-based)
- `at_ms`: millisegundos relativos ao **início do clip** (não do vídeo)
- `scale`: fator de escala (1.0 = sem zoom, 1.3 = máximo recomendado)
- `transform_x / transform_y`: deslocamento horizontal/vertical (0.0 a ±0.2)

**Padrões recomendados:**
- Hook de abertura: `1.0→1.15` ao longo de 2000ms (ken-burns suave)
- Punch-in em revelação: `1.0→1.2` em 300ms (rápido)
- Emotivo/storytelling: `1.0→1.08` ao longo do clip inteiro

### `assets_needed[]`
Lista de filenames esperados em `<input>/assets/`. Se declarados e não encontrados, o pipeline bloqueia na fase 5 e mostra o manifest.

### `color_correction`
Aplicado globalmente via `cssFilter` no `VideoCut.tsx`:
- `contrast`: multiplicador (1.0 = neutro)
- `saturation`: multiplicador (1.0 = neutro)
- `brightness`: offset (-1.0 a 1.0)
- `color_grade`: `"warm"` | `"cool"` | `"cinematic"` | `"neutral"`

### `rich_overlays[]` — DIRECTOR-LEVEL VISUAL STORYTELLING (obrigatório, mín 6 entries)

Animações ricas que VISUALIZAM os conceitos do speaker. NÃO são captions ou stat-overlays simples.
Cada entrada tem `kind` (discriminador) + `start`/`end` em segundos do timeline final + props específicas:

| `kind` | Quando usar | Props principais |
|---|---|---|
| `roman_scroll_wipe` | Pivot temporal/histórico | `direction: "left" \| "right"` |
| `roman_columns_bg` | Background de seção histórica | `opacity: 0.10-0.25` |
| `vespasian_bust` | Personagem histórico romano | `position: "left" \| "right" \| "center"` |
| `roman_latrine` | Banheiros romanos (humor visual) | — |
| `gold_coin_drop` | Moeda caindo + flash + bounce | `land_at: <s no timeline em que pousa>` |
| `cinematic_title` | Título serif fullscreen (frase mítica/latim) | `text`, `subtitle?`, `font_family?` |
| `year_caption` | Caption serif curto ("ROMA — 70 d.C.") | `text`, `position` |
| `code_document` | Página de lei sobreposta com artigo | `article: "118"`, `title?` |
| `highlighter_underline` | Marca-texto sob caption | — (posicionamento auto) |
| `stamp_brand` | Selo circular rotacionando (top-corner) | `text`, `position` |
| `stf_stamp` | Brasão STF impacto + shake | `text` |
| `ticker_resp` | Lista vertical scrolling REsps mono | `items: [...]` |
| `tributavel_stamp` | "TRIBUTÁVEL" stamp grande | `text` |
| `split_comparison` | 2 ícones lado a lado (A vs B) | `left_icon`, `right_icon`, `left_label`, `right_label` |
| `merge_into_keyword` | Texto destaque central pós-split | `text` |
| `scale_of_justice` | Balança desnivelando (isonomia) | `left_weight`, `right_weight` (0.5-1.5) |
| `context_tags` | Pills flutuantes ao redor de número | `tags: [...]` |
| `counter_number` | Number animation 0→target fullscreen | `from?`, `to`, `suffix?`, `subtitle?` |
| `data_network` | Rede de dots conectados (Receita) | `node_count: ~60-100` |
| `mismatch_cards` | 2 cards desproporcionais (declarado vs real) | `declared_label`, `declared_value`, `actual_label`, `actual_value` |
| `warm_shift_pivot` | Color shift radial cobre (problema→solução) | — |
| `tribotax_shield` | Escudo + check + docs orbitando | `show_orbit: true` |
| `comment_bubble_cta` | Balão de comentário + arrow CTA | `keyword: "PATRIMÔNIO"` |

**Regras de uso:**
1. **Mín 6 entradas** para reels de 60-90s. Máx 25.
2. **Mapeie cada substantivo concreto** (moeda, balança, lei, dado) a um overlay.
3. **Punctue conceitos abstratos** (latim, citações, números) com `cinematic_title` ou `counter_number`.
4. **Pivots conceituais** = `roman_scroll_wipe`, `warm_shift_pivot` (não use só `transitions:fade`).
5. **Overlay sobre Alex** quando ele explica; **fullscreen gráfico** em punch moments. Máx 4s fullscreen seguido.
6. **Sincronize com beats** do voice-over (palavras-chave, pausas dramáticas).
