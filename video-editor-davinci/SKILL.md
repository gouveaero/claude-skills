---
name: video-editor-davinci
description: Use when the user wants to edit a video, montar um Reel/Short/TikTok, criar timeline no DaVinci Resolve a partir de clipes brutos, gerar legendas word-level dinâmicas, aplicar cortes automáticos sincronizados com áudio, ou produzir motion graphics que ilustram o que está sendo falado. Ativa em frases como "edita esse vídeo", "monta o reel", "gera a timeline no DaVinci", "corta esses clipes", "legenda dinâmica estilo Submagic", "legenda word-by-word", "vídeo curto pra Instagram". Generalista — funciona para qualquer cliente via `<ClientFolder>/.video-editor.json`. Entrega projeto DaVinci Resolve Studio editável (não MP4 final), preservando controle criativo.
---

# video-editor-davinci

Skill que recebe clipes de vídeo + (opcional) roteiro markdown e monta uma **timeline editável no DaVinci Resolve Studio** com cortes dinâmicos, legendas word-level, lower-thirds, stat numbers e color presets — tudo aplicado nativamente via API Python do Resolve. O usuário abre o projeto e refina; nada de output MP4 fechado.

## Quando usar

**Sintomas que disparam a skill:**
- Gabriel tem clipes filmados (ele falando ou B-roll) e quer um Reel/Short montado
- Quer legenda dinâmica estilo Submagic / CapCut / Opus Clip — destaque palavra-a-palavra
- Quer cortes ritmados sincronizados com beats da fala
- Quer overlays gráficos (números, citações de processos jurídicos, lower-thirds com nome) ilustrando o que está sendo dito
- Quer iterar: ajustar o `edit_plan.json` e rebuildar a timeline sem refazer tudo

**Quando NÃO usar:**
- Roteiro ainda não existe → use `vhoe-roteiro` ou `copywriting` antes
- Voiceover/TTS necessário → outras skills
- Carrossel estático → use `carousel-generator`
- Color grading manual fino → DaVinci Studio nativo é melhor que automação

## Pré-requisitos

A skill **só roda se o setup local estiver pronto**. Sempre comece executando:

```bash
python3 ~/.claude/skills/video-editor-davinci/scripts/check_setup.py
```

Se algo faltar, leia [references/setup.md](references/setup.md) e siga as instruções. Não tente prosseguir com setup incompleto — vai falhar feio.

**Requisitos resumidos:**
- DaVinci Resolve **Studio** instalado e aberto (free não suporta scripting externo)
- Variáveis de ambiente `RESOLVE_SCRIPT_API`, `RESOLVE_SCRIPT_LIB`, `PYTHONPATH` configuradas no shell rc
- Resolve → Preferences → System → General → External Scripting = "Local"
- `brew install ffmpeg`
- `pip3 install pydavinci mlx-whisper jinja2 anthropic`
- Para v2 (Remotion overlays custom): `npm install` em `remotion/`

## Config por projeto

Cada projeto/cliente tem seu próprio `.video-editor.json` na raiz da pasta do cliente. A skill sobe no diretório atual procurando esse arquivo (mesmo padrão de `meta-ads-operator`, `imagens-freepik`).

Ver [brand-configs/_example.json](brand-configs/_example.json) para template completo. Mínimo viável:

```json
{
  "brand": {
    "name": "TriboTax",
    "primary_color": "#1F4D2C",
    "accent_color": "#B87333",
    "font_family": "Inter",
    "font_weight_caption": 800
  },
  "defaults": {
    "aspect": "9:16",
    "fps": 30,
    "caption_style": "highlight_accent"
  }
}
```

A skill também lê o `CLAUDE.md` do projeto (se existir) para puxar regras de marca/voz/compliance — ex: TriboTax tem regras OAB, Vhoe tem tom de aviação militar.

## Pipeline — o que a skill faz

```
clipes brutos      ┌─→ [2] mlx-whisper transcreve word-level
+ roteiro.md ──────┤
(ou só clipes)     └─→ [3] LLM plan_edit ─→ edit_plan.json
                                              │
                                              └─→ [4] pydavinci dirige Resolve:
                                                    - cria projeto + timeline
                                                    - importa clipes ao MediaPool
                                                    - posiciona cortes em V1
                                                    - injeta Fusion macros (.drfx) em V2/V3
                                                    - monta Subtitle track word-level
                                                    - aplica color presets
                                                    │
                                                    └─→ [5] preview MP4 + handoff
```

## Comandos principais

### 1. Setup (primeira vez)
```bash
python3 scripts/check_setup.py
```
Valida ambiente. Roda primeiro **sempre**.

### 2. Pipeline completo (clipes + roteiro)
Modo padrão, esperado quando há `roteiro.md` na pasta de clipes:

```bash
python3 scripts/build_reel.py \
    --input <pasta_com_clipes> \
    --script <pasta_com_clipes>/roteiro.md \
    --name "alex_pecunia_non_olet"
```

Faz transcribe → plan_edit → build_timeline → preview render. Output em `<ClientFolder>/output/<name>/`.

### 3. Pipeline em etapas (controle granular)
```bash
python3 scripts/transcribe.py --input <clips_dir>          # → transcripts.json
python3 scripts/plan_edit.py --transcripts t.json --script s.md  # → edit_plan.json
python3 scripts/build_timeline.py --plan edit_plan.json --name <name>  # → projeto Resolve
python3 scripts/preview_render.py --project <name>         # → preview.mp4
```

Útil quando você quer editar o `edit_plan.json` à mão antes de buildar.

### 4. Rebuild rápido
Editou `edit_plan.json` e quer só refazer a timeline sem retranscrever:
```bash
python3 scripts/build_timeline.py --plan edit_plan.json --name <name> --rebuild
```

### 5. Modo discover (raw footage sem ordem) — v1.5
```bash
python3 scripts/build_reel.py \
    --input <pasta_com_clipes_brutos> \
    --mode discover \
    --intent "explicação sobre Pecunia Non Olet em 30s" \
    --name "alex_pecunia_v1"
```

Skill assiste cada clipe via Vision, ordena por beats narrativos, então roda pipeline normal.

## Estrutura de input esperada

**Modo padrão (clipes + roteiro):**
```
TriboTax/material_bruto/reel_pecunia/
├── 01_intro.mp4
├── 02_explicacao.mp4
├── 03_b_roll_processo.mp4
├── 04_cta.mp4
└── roteiro.md           ← opcional mas recomendado
```

`roteiro.md` deve seguir o padrão do `vhoe-roteiro` ou similar — texto da narração + indicações de B-roll/cuts/overlays.

**Modo discover (raw):**
```
TriboTax/material_bruto/reel_aleatorio/
├── IMG_4521.mov
├── IMG_4522.mov
├── IMG_4523.mov
└── (sem ordem ou roteiro)
```

Skill descobre conteúdo por transcrição + Vision e propõe ordem.

## Output

```
<ClientFolder>/output/<reel_name>/
├── <reel_name>.drp          # projeto DaVinci salvo
├── <reel_name>_preview.mp4  # render rápido pra validar
├── edit_plan.json           # plano editado (memória pra iteração)
├── transcripts.json         # cache de transcrição
└── assets/                  # clipes originais (referenciados pelo MediaPool)
```

Skill mostra ao final:
> "Projeto pronto: TriboTax/output/<name>. Abra DaVinci Resolve → vai aparecer em Project Manager. Para iterar, edite `edit_plan.json` e rode com `--rebuild`."

## Macros Fusion (.drfx) disponíveis

Ver [references/macro-library.md](references/macro-library.md) para detalhes de cada uma e seus parâmetros.

| Macro | Uso | Parâmetros principais |
|-------|-----|----------------------|
| `caption_word_highlight` | Legenda word-level estilo Reels | `words[]`, `style`, `position` |
| `lower_third` | Identificação de pessoa/conceito | `title`, `subtitle`, `color` |
| `stat_number` | Número/estatística animada | `value`, `label`, `prefix` |
| `callout_arrow` | Seta apontando elemento na tela | `text`, `target_xy` |
| `transition_swipe` | Transição entre cortes | `direction`, `duration` |

Macros customizadas: criar manualmente no Fusion uma vez, salvar como `.drfx` em `templates/macros/`, documentar parâmetros em `references/macro-library.md`.

## Estilos de legenda

Ver [references/caption-styles.md](references/caption-styles.md). Presets atuais:

- `highlight_accent`: palavra atual destacada na cor accent do brand (Submagic-like)
- `highlight_box`: caixa colorida atrás da palavra atual
- `bouncy`: cada palavra entra com bounce (TikTok-like)
- `minimal`: branco, sem highlight, fonte fina (corporate)
- `karaoke`: progressive fill word-by-word (legível em mute)

## Hard rules

1. **Nunca rode sem `check_setup.py` passando**. Se Resolve não está aberto, scripts vão falhar com erro críptico.
2. **Sempre lê `.video-editor.json` do projeto antes de gerar conteúdo** — não invente cores/fontes.
3. **Sempre lê `CLAUDE.md` do projeto se existir** — regras de compliance/voz são críticas (ex: OAB no Tribotax).
4. **Output sempre em `<ClientFolder>/output/<reel_name>/`**, nunca em pastas dispersas.
5. **Nunca delete material_bruto** — apenas referencia ou copia trimado para `assets/`.
6. **Plan_edit JSON é fonte de verdade** — a timeline é deriva do plan, não o contrário. Para iterar, sempre edite o JSON.
7. **Não tente automatizar color grading fino** — sai feio. Aplique presets simples e deixe o Gabriel refinar.

## Edge cases

- **Resolve fechado**: `check_setup.py` detecta e instrui abrir. Build_timeline falha cedo com mensagem clara.
- **Clipes com framerates mistos**: Resolve handle se config_timeline = primeiro clipe. Skill avisa se mistura.
- **Áudio só (sem vídeo)**: skill cria timeline com placeholder visual (background gradient + waveform animation).
- **Roteiro mais longo que clipes**: skill avisa, sugere modo discover ou mais material.
- **Clipes verticais 9:16 misturados com horizontal**: skill detecta e aplica reframe automático (Resolve Smart Reframe via API).

## Próximas iterações (não implementadas ainda)

- v1.5: modo discover (raw footage ordering via Whisper + Vision + embeddings)
- v2: Remotion como motor de overlays custom (data viz dinâmica, kinetic typography fora do padrão Fusion)
- v2: integração com `vhoe-roteiro` — chama essa skill direto após roteiro pronto
- v2: music selection automático (royalty-free libs) com sync de beats
- v3: B-roll generation via stock APIs (Pexels, Storyblocks) quando não há material filmado
