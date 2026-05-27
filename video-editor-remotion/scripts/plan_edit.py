#!/usr/bin/env python3
"""
plan_edit.py — turns transcripts + roteiro into an edit_plan.json (Remotion-flavored).

Adapted from video-editor-davinci. Schema differs:
- color_correction uses css_filter (CSS string) instead of ASC CDL tuples
- adds `transitions` array (between cuts)
- adds `audio_sync_beats` array (timestamps for caption emphasis)
- adds `sfx[]` (sound effects, categories from sfx_index)
- adds `zoom_keyframes[]` (cinematic camera moves)
- adds `assets_needed[]` (external assets)
- adds `aspect` field (9:16 | 16:9)

Two planner backends:
- `--planner api` (default): calls the Anthropic SDK with ANTHROPIC_API_KEY
- `--planner agent`: skips the API call, writes a planning brief next to --output
  and exits 2. Use this when the caller is itself a Claude Code agent (no
  separate API key needed) — the agent reads the brief and writes the final
  edit_plan.json directly with Read/Write tools. If ANTHROPIC_API_KEY is
  missing and --planner is unset, falls back to `agent` mode automatically.

Usage:
    python3 plan_edit.py --transcripts transcripts.json --brand-config /path/to/.video-editor.json
                         [--script roteiro.md] [--claude-md /path/to/CLAUDE.md]
                         --output edit_plan.json [--target-duration 30]
                         [--model claude-sonnet-4-6] [--planner api|agent]
                         [--sfx-index sfx_index.json]
                         [--best-practices best-practices-notebooklm.md]
                         [--aspect 9:16|16:9]

Uses prompt caching (api mode): system prompt + brand config + claude.md cached.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:  # only required for --planner=api
    anthropic = None

DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an expert short-form video editor specializing in vertical Reels/TikToks/Shorts. You produce machine-readable edit plans that drive a Remotion (React) composition.

# Your job

Given: raw clip transcriptions (word-level timestamps) + a roteiro (script, optional) + brand config + project rules.

Output: a single JSON object describing the final edit. NOTHING ELSE — no preamble, no markdown fences. Just JSON.

# Output schema

{
  "name": "<short kebab-case name>",
  "duration_target_seconds": <number>,
  "aspect": "9:16" | "16:9",
  "fps": 30,
  "resolution": [1080, 1920],
  "v1_main": [
    {
      "clip": "<filename from transcripts>",
      "source_in": <seconds in source clip>,
      "source_out": <seconds in source clip>,
      "timeline_start": <seconds in final timeline>,
      "rationale": "<one short line: why this take, why this trim>"
    }
  ],
  "transitions": [
    {"after_cut_index": <int, 0-based>, "type": "fade" | "slide_up" | "wipe" | "none", "duration_frames": <int 0-15>}
  ],
  "subtitle_track": [
    {
      "text": "<UPPERCASE 1-4 words max>",
      "start": <seconds in final timeline>,
      "end": <seconds in final timeline>,
      "style": "highlight_accent" | "highlight_box" | "minimal",
      "emphasis": "keyword" | "emphasis" | "normal"
    }
  ],
  "overlays_v2": [
    {"text": "<big stat e.g. 37%>", "subtext": "<line below>", "start": <s>, "end": <s>}
  ],
  "rich_overlays": [
    /* DIRECTOR-LEVEL visual storytelling — see catalog below.
       MINIMUM 6 entries for a 60-90s reel. Use these to VISUALIZE concepts the speaker is explaining.
       Examples: gold coin animation when "money" is mentioned, scale of justice for "isonomia",
       data network for "cruzamento de dados", scroll wipe for historical pivot, etc. */
    {"kind": "<one of catalog>", "start": <s>, "end": <s>, /* + kind-specific props */}
  ],
  "audio_sync_beats": [<seconds in final timeline where there is musical/vocal emphasis>],
  "color_correction": {
    "css_filter": "saturate(0.92) contrast(1.05) brightness(1.04) hue-rotate(-3deg)"
  },
  "render_preset": "h264_master_q18"
}

# Editing principles

1. **Aggressive cutting**: clips on V1 should be 1-4s each. Cut filler ("é...", "tipo", "então..."), repeated takes, breath pauses. Pick THE best take of each beat.
2. **Caption density**: 1-3 words per subtitle entry, max 4. Total caption coverage ≈ 90% of speech.
3. **CAPS for captions**: text field always UPPERCASE.
4. **Subtitle timing**: align to word_timestamps from transcripts — start when the word starts, end ~50ms after last word.
5. **Source IN/OUT precision**: use the word_timestamps to find clean cut points (silence between words). Don't cut mid-word.
6. **Timeline_start**: must be sequential, no gaps unless intentional. Compute as cumulative duration.
7. **Transitions**: default `none` for hard cuts (most cases). Use `fade`/`slide_up` only when narrative beat shifts. Duration 4-8 frames.
8. **css_filter**: keep the look subtle. Default warm/contrasty: `saturate(0.92) contrast(1.05) brightness(1.04)`.
9. **Brand voice**: respect brand config. Respect CLAUDE.md compliance rules (e.g., OAB rules — no guarantees).

# Forbidden

- Never invent clips that aren't in the transcripts.
- Never produce timeline gaps (timeline_start[i+1] = timeline_start[i] + (source_out[i] - source_in[i])).
- Never exceed duration_target_seconds by more than 10%.
- Never output anything but the JSON object.

## Novos campos obrigatórios no edit_plan.json

### sfx[] — efeitos sonoros
Declare efeitos sonoros usando APENAS as categorias disponíveis no sfx_index.
Para cada momento sonoro relevante:
{
  "at_ms": <millisegundos desde o início>,
  "category": "<CATEGORIA_DO_SFX_INDEX>",
  "intent": "<descrição de por que esse SFX aqui>",
  "volume_db": <número negativo, ex: -10>
}
Regras de uso (use APENAS categorias que existem no sfx_index injetado abaixo):
- RISER: build-up antes de grandes revelações, hook de abertura, tensão crescente
- WOOSH: TODA transição de cena/cut seco, swipe in/out, overlay enter
- PLIM: destacar números, check-marks, revelações positivas, notificações suaves
- CINEMATICA: momento de maior impacto do vídeo, drop dramático, CTA final
- GLITCH: pattern interrupts, virada de narrativa, problema/erro
- DIGITAL: overlay digital aparecendo, tech reveal, UI moderna
- CAMERA: reveal visual, zoom-in para detalhe, product shot
- CLICK: CTAs, items de checklist, tap em botão
- DINHEIRO: menção de valor monetário, savings, revenue (ka-ching)
- TECLADO: digitação, kinetic text, work scene
- CONTAGEM: countdown antes de revelar stat, tick-tock
- ROLAGEM: lista rolando, counter mecânico, progress
- TRANSIÇÃO: transição genérica suave entre cenas longas
- AMBIENTE: ambiente de fundo (b-roll, intro contemplativa) — volume bem baixo (-18 dB)
- ESTALO: ênfase em palavra-chave, marcação rítmica
- POPS: pop-up de elemento, balão aparecendo, badge entrando
- VARIAVEIS: especiais (épico, idea moment, error moment)
- BOOM: drop dramático, explosão visual, bass impact (use COM PARCIMÔNIA, 1x por reel max)
- NOTIFICATION: feedback de UI, success/error chime (notificações fortes)
- DRUM: kick/snare rítmico, percussion accent
- GLASS_BREAK: quebra de paradigma, destruição visual, "quebrando regras"
- APPLAUSE: celebração, vitória, "parabéns" momento
- HORROR: suspense, jump-scare, momento dark (use COM CUIDADO — só se fit narrativo)
- FAIL: sad trombone, comédia error meme, falha cômica
- MAGIC: sparkle, twinkle, momento mágico/positivo
- HEARTBEAT: antecipação lenta, medo crescente, tensão pré-revelação
Mínimo 3 SFX por vídeo. Máximo 12. Volume típico -6 a -12 dB (voz = 0 dB).

### zoom_keyframes[] — zooms cinematográficos
Declare zoom keyframes para clips que merecem movimento de câmera:
{
  "clip_idx": <índice no v1_main>,
  "at_ms": <ms relativo ao início do clip>,
  "scale": <1.0 a 1.3>,
  "transform_x": <-0.2 a 0.2, opcional>,
  "transform_y": <-0.2 a 0.2, opcional>
}
Use zoom_keyframes em:
- Hook de abertura: zoom lento de 1.0→1.15 durante os primeiros 2s
- Revelação de número/stat: punch-in rápido 1.0→1.2 em 300ms
- Emotivo/storytelling: ken-burns 1.0→1.1 ao longo do clip

### assets_needed[] — assets externos
Liste filenames de qualquer logo, imagem, gráfico ou b-roll externo que o vídeo precisa.
Ex: ["logo.png", "grafico_crescimento.png", "foto_produto.jpg"]
Se não precisar de assets externos, use [].

### aspect
Defina "9:16" (vertical, Reels/TikTok/Shorts) ou "16:9" (horizontal, YouTube).
Isso afeta safe areas das legendas, tamanho de texto e crop dos clips.

# DIRECTOR-LEVEL VISUAL STORYTELLING (rich_overlays[]) — OBRIGATÓRIO

Captions + zooms + SFX por si só ficam BÁSICOS. Para um Reel digno, você TEM que VISUALIZAR
os conceitos que o speaker está explicando, usando overlays animados ricos.

## Princípios de direção

1. **Visualize os substantivos concretos**: se o speaker fala "moeda de ouro", anime uma moeda.
   Se fala "balança da justiça", mostre uma balança. Se fala "rede de dados", mostre uma rede.
2. **Punctue conceitos abstratos com kinetic titles**: terminologia técnica em latim, números
   importantes (37%, R$ 4.2M), citações filosóficas — vire tela cheia gráfica por 2-4s.
3. **Pivot temporal/conceitual = transição visual ritualizada**: pivot histórico = pergaminho
   desenrolando; problema→solução = color shift + shield aparecendo. Não use só fade.
4. **Overlay sobre Alex** quando ele está EXPLICANDO. **Fullscreen gráfico** em momentos
   de PUNCH (revelações, números, citações). Nunca mais que 4s de fullscreen seguido.
5. **Sincronize com beats**: ancore animações em sílabas tônicas / palavras-chave.
6. **Mínimo 6 rich_overlays por reel de 60-90s**. Máximo 25.

## Catálogo de rich_overlays disponíveis (componentes Remotion prontos)

Todos têm `start` e `end` em segundos do timeline final. Cada `kind` tem props específicas:

```jsonc
// HISTÓRICOS / NARRATIVOS
{"kind": "roman_scroll_wipe", "start": 8.5, "end": 9.7, "direction": "right"}
{"kind": "roman_columns_bg", "start": 9.2, "end": 23.6, "opacity": 0.18}     // background coliseu
{"kind": "vespasian_bust", "start": 13.4, "end": 19.0, "position": "right"}  // bust romano cobre
{"kind": "roman_latrine", "start": 16.5, "end": 19.1}                         // ícone latrina ancient
{"kind": "gold_coin_drop", "start": 19.3, "end": 21.3, "land_at": 20.3}      // moeda gira/cai/flash
{"kind": "year_caption", "start": 13.5, "end": 16.2, "text": "ROMA — 70 d.C.", "position": "bottom-left"}

// TÍTULOS CINEMÁTICOS / TIPOGRÁFICOS
{"kind": "cinematic_title", "start": 19.8, "end": 23.4, "text": "PECUNIA NON OLET",
 "subtitle": "o dinheiro não tem cheiro", "font_family": "serif"}    // FULLSCREEN serif title

// JURÍDICOS / DOCUMENTAIS
{"kind": "code_document", "start": 23.8, "end": 32.85, "article": "118",
 "title": "CÓDIGO TRIBUTÁRIO NACIONAL"}                              // documento overlay
{"kind": "highlighter_underline", "start": 29.0, "end": 30.5}        // marcador cobre
{"kind": "stamp_brand", "start": 3.5, "end": 7.5, "text": "ART. 118 CTN", "position": "top-right"}
{"kind": "stf_stamp", "start": 43.2, "end": 47.3, "text": "STF — PACIFICADO"}  // brasão impacto
{"kind": "ticker_resp", "start": 43.2, "end": 50.0,
 "items": ["RESP 1.493.162", "RESP 779.230"]}                        // jurisprudência rolando
{"kind": "tributavel_stamp", "start": 76.5, "end": 78.2, "text": "TRIBUTÁVEL"}

// COMPARAÇÕES / CONCEITUAIS
{"kind": "split_comparison", "start": 35.5, "end": 38.85,
 "left_icon": "padaria", "right_icon": "shadow",
 "left_label": "PADARIA", "right_label": "OPERAÇÃO CRIMINOSA"}        // dois cards lado a lado
{"kind": "merge_into_keyword", "start": 38.85, "end": 42.85, "text": "ACRÉSCIMO PATRIMONIAL"}
{"kind": "scale_of_justice", "start": 50.1, "end": 54.5,
 "left_weight": 0.5, "right_weight": 1.5}                            // balança desnivelando
{"kind": "mismatch_cards", "start": 73.5, "end": 78.0,
 "declared_label": "DECLARADO", "declared_value": "R$ 80k",
 "actual_label": "PATRIMÔNIO", "actual_value": "R$ 4.2M"}            // cards desproporcionais

// NÚMEROS / DADOS
{"kind": "counter_number", "start": 61.4, "end": 64.0,
 "from": 0, "to": 37, "suffix": "%", "subtitle": "carga tributária"}  // counter animado fullscreen
{"kind": "context_tags", "start": 61.4, "end": 64.0,
 "tags": ["IRPJ", "CSLL", "PIS", "COFINS"]}                          // pills flutuantes ao redor
{"kind": "data_network", "start": 64.2, "end": 73.0, "node_count": 80}  // rede de dados conectados

// PIVOT / CTA TRIBOTAX
{"kind": "warm_shift_pivot", "start": 77.8, "end": 78.8}             // color shift radial cobre
{"kind": "tribotax_shield", "start": 78.5, "end": 87.2, "show_orbit": true}  // escudo + docs orbitando
{"kind": "comment_bubble_cta", "start": 90.0, "end": 92.3, "keyword": "PATRIMÔNIO"}
```

## Como mapear conceitos do speaker → rich_overlays

| Speaker fala sobre... | rich_overlay sugerido |
|---|---|
| Roma Antiga / história | `roman_scroll_wipe` + `roman_columns_bg` + `year_caption` |
| Imperador / personagem histórico | `vespasian_bust` (adapte coin) |
| Dinheiro caindo / moeda | `gold_coin_drop` |
| Citação latina / mítica | `cinematic_title` (serif fullscreen) |
| Código de lei / artigo | `code_document` + `highlighter_underline` |
| Decisão STF / autoridade | `stf_stamp` + opcional `ticker_resp` |
| Comparação A vs B | `split_comparison` + `merge_into_keyword` |
| Princípio de igualdade / desequilíbrio | `scale_of_justice` |
| Número/percentual destacado | `counter_number` (animação 0→target) |
| Categorias múltiplas | `context_tags` (pills flutuantes) |
| Cruzamento de dados / análise | `data_network` |
| Diferença numérica / mismatch | `mismatch_cards` |
| Pivot problema → solução | `warm_shift_pivot` + componente da solução |
| Marca/proteção/escudo | `tribotax_shield` |
| Call to action / comentar | `comment_bubble_cta`"""


def _build_sfx_summary(sfx_index: dict) -> str:
    """Build a compact human-readable summary of SFX categories from sfx_index."""
    lines = ["## SFX disponíveis (use APENAS estas categorias):"]
    categories = sfx_index.get("categories", {})
    for cat, data in sorted(categories.items()):
        files = data.get("files", [])
        desc = data.get("description", "")
        lines.append(f"{cat}: {desc} ({len(files)} variações)")
    return "\n".join(lines)


def build_user_message(transcripts, script, brand_config, claude_md, target_duration,
                       name_hint, sfx_index=None, aspect="9:16"):
    parts = []
    parts.append("# Brand config\n```json\n" + json.dumps(brand_config, ensure_ascii=False, indent=2) + "\n```")
    if claude_md:
        parts.append("# Project CLAUDE.md (compliance + voice)\n" + claude_md.strip())
    if script:
        parts.append("# Roteiro\n" + script.strip())
    else:
        parts.append("# Roteiro\n(no script — infer narrative from transcripts)")
    compact = {
        "language": transcripts.get("language"),
        "clips": {
            name: {
                "duration": clip.get("duration"),
                "text": clip.get("text"),
                "words": [{"w": w["word"], "s": w["start"], "e": w["end"]} for w in clip.get("words", [])],
            }
            for name, clip in transcripts.get("clips", {}).items()
        }
    }
    parts.append("# Transcripts (word-level)\n```json\n" + json.dumps(compact, ensure_ascii=False) + "\n```")
    parts.append(f"# Target duration\n{target_duration} seconds (±10%)")
    parts.append(f"# Aspect ratio\n{aspect}")
    if name_hint:
        parts.append(f"# Suggested name\n{name_hint}")

    # Inject SFX index summary if provided
    if sfx_index:
        parts.append(_build_sfx_summary(sfx_index))

    parts.append("\nProduce the edit_plan.json now. JSON only.")
    return "\n\n".join(parts)


def write_planning_brief(brief_path, transcripts, script_text, brand_config, claude_md_text,
                         target_duration, name_hint, output_path, sfx_index=None, aspect="9:16"):
    """Write a markdown brief that a Claude Code agent can read to produce edit_plan.json by hand."""
    parts = []
    parts.append(f"# Planning brief — manual mode\n")
    parts.append(f"You (Claude Code agent) must write `{output_path}` by hand based on the inputs below.")
    parts.append(f"After you write the JSON, run `build_remotion.py --plan {output_path} ...` to compile.\n")
    parts.append("## Output schema (the JSON you must write)\n")
    parts.append("```\n" + SYSTEM_PROMPT.split("# Output schema\n\n", 1)[1].split("\n\n# Editing principles", 1)[0] + "\n```\n")
    parts.append("## Editing principles\n")
    parts.append(SYSTEM_PROMPT.split("# Editing principles\n\n", 1)[1].split("\n\n# Forbidden", 1)[0] + "\n")
    parts.append("## Forbidden\n")
    parts.append(SYSTEM_PROMPT.split("# Forbidden\n\n", 1)[1].strip() + "\n")
    parts.append("## Brand config\n```json\n" + json.dumps(brand_config, ensure_ascii=False, indent=2) + "\n```\n")
    if claude_md_text:
        parts.append("## CLAUDE.md (compliance)\n" + claude_md_text.strip() + "\n")
    if script_text:
        parts.append("## Roteiro\n" + script_text.strip() + "\n")
    compact = {
        "language": transcripts.get("language"),
        "clips": {
            name: {
                "duration": clip.get("duration"),
                "text": clip.get("text"),
                "words": [{"w": w["word"], "s": w["start"], "e": w["end"]} for w in clip.get("words", [])],
            }
            for name, clip in transcripts.get("clips", {}).items()
        },
    }
    parts.append("## Transcripts (word-level)\n```json\n" + json.dumps(compact, ensure_ascii=False) + "\n```\n")
    parts.append(f"## Target duration\n{target_duration} seconds (±10%)\n")
    parts.append(f"## Aspect ratio\n{aspect}\n")
    if name_hint:
        parts.append(f"## Suggested name\n`{name_hint}`\n")
    if sfx_index:
        parts.append("## SFX disponíveis\n" + _build_sfx_summary(sfx_index) + "\n")
    brief_path.write_text("\n".join(parts), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcripts", required=True, type=Path)
    ap.add_argument("--script", type=Path)
    ap.add_argument("--brand-config", required=True, type=Path)
    ap.add_argument("--claude-md", type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--target-duration", type=float, default=30.0)
    ap.add_argument("--name", help="Kebab-case name hint")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--planner", choices=["api", "agent"], default=None,
                    help="api: call Anthropic SDK (needs ANTHROPIC_API_KEY). "
                         "agent: write planning brief and exit 2 — caller (Claude Code agent) "
                         "writes edit_plan.json directly. "
                         "Default: api if ANTHROPIC_API_KEY is set, else agent.")
    # New arguments
    ap.add_argument("--sfx-index", type=Path, default=None,
                    help="Path to sfx_index.json — informs AI of available SFX categories")
    ap.add_argument("--best-practices", type=Path, default=None,
                    help="Path to best-practices-notebooklm.md — injected as cached context")
    ap.add_argument("--aspect", choices=["9:16", "16:9"], default="9:16",
                    help="Output aspect ratio (default: 9:16 for Reels/TikTok/Shorts)")
    args = ap.parse_args()

    transcripts = json.loads(args.transcripts.read_text())
    brand_config = json.loads(args.brand_config.read_text())
    script_text = args.script.read_text() if args.script and args.script.exists() else None
    claude_md_text = args.claude_md.read_text() if args.claude_md and args.claude_md.exists() else None

    # Load optional new inputs
    sfx_index = None
    if args.sfx_index and args.sfx_index.exists():
        sfx_index = json.loads(args.sfx_index.read_text())
        print(f"  SFX index loaded: {len(sfx_index.get('categories', {}))} categories")
    elif args.sfx_index:
        print(f"  [WARN] --sfx-index not found: {args.sfx_index}")

    best_practices_text = None
    if args.best_practices and args.best_practices.exists():
        best_practices_text = args.best_practices.read_text()[:8000]
        print(f"  Best practices loaded: {len(best_practices_text)} chars")
    elif args.best_practices:
        print(f"  [WARN] --best-practices not found: {args.best_practices}")

    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    planner = args.planner or ("api" if has_key else "agent")

    if planner == "agent":
        brief_path = args.output.with_name(args.output.stem + "_brief.md")
        write_planning_brief(brief_path, transcripts, script_text, brand_config,
                             claude_md_text, args.target_duration, args.name, args.output,
                             sfx_index=sfx_index, aspect=args.aspect)
        print(f"Planner=agent — wrote brief to {brief_path}")
        print(f"   Next: as the Claude Code agent, read the brief and write {args.output} directly.")
        print(f"   Then run build_remotion.py --plan {args.output} ...")
        sys.exit(2)

    # planner == "api"
    if anthropic is None:
        sys.exit("anthropic SDK not installed. `pip install anthropic` or use --planner=agent.")
    if not has_key:
        sys.exit("ANTHROPIC_API_KEY not set. Use --planner=agent to skip the API.")

    client = anthropic.Anthropic()
    user_message = build_user_message(
        transcripts, script_text, brand_config, claude_md_text,
        args.target_duration, args.name,
        sfx_index=sfx_index, aspect=args.aspect
    )

    # Build system blocks with optional best-practices cache
    if best_practices_text:
        system_blocks = [
            {
                "type": "text",
                "text": f"# Best Practices (NotebookLM)\n{best_practices_text}",
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            },
        ]
    else:
        system_blocks = [
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
        ]

    print(f"Calling {args.model} ({len(user_message)} chars)...")
    response = client.messages.create(
        model=args.model,
        max_tokens=8000,
        system=system_blocks,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("\n", 1)[0]
        if raw.startswith("json"):
            raw = raw.split("\n", 1)[1]

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as e:
        debug_path = args.output.with_suffix(".raw.txt")
        debug_path.write_text(raw)
        sys.exit(f"Invalid JSON: {e}\n   Saved raw to {debug_path}")

    required = {"name", "duration_target_seconds", "aspect", "fps", "v1_main", "subtitle_track"}
    missing = required - set(plan.keys())
    if missing:
        sys.exit(f"Missing keys: {missing}")

    # Defaults for fields
    plan.setdefault("transitions", [])
    plan.setdefault("overlays_v2", [])
    plan.setdefault("audio_sync_beats", [])
    plan.setdefault("color_correction", {"css_filter": "saturate(0.92) contrast(1.05) brightness(1.04)"})
    plan.setdefault("render_preset", "h264_master_q18")
    # Defaults for new fields
    plan.setdefault("sfx", [])
    plan.setdefault("zoom_keyframes", [])
    plan.setdefault("assets_needed", [])
    # Respect CLI aspect if AI didn't produce one matching the flag
    if args.aspect and plan.get("aspect") != args.aspect:
        plan["aspect"] = args.aspect

    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2))

    usage = response.usage
    cache_hit = getattr(usage, "cache_read_input_tokens", 0) or 0
    print(f"Wrote {args.output}")
    print(f"   Tokens: in={usage.input_tokens} out={usage.output_tokens} cache_read={cache_hit}")
    print(f"   Plan: {len(plan['v1_main'])} cuts, {len(plan['subtitle_track'])} captions, "
          f"{len(plan.get('overlays_v2', []))} stats, {len(plan.get('sfx', []))} SFX, "
          f"{len(plan.get('zoom_keyframes', []))} zoom-kf, target {plan['duration_target_seconds']}s")


if __name__ == "__main__":
    main()
