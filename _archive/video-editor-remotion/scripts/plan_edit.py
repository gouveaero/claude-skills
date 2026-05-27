#!/usr/bin/env python3
"""
plan_edit.py — turns transcripts + roteiro into an edit_plan.json (Remotion-flavored).

Adapted from video-editor-davinci. Schema differs:
- color_correction uses css_filter (CSS string) instead of ASC CDL tuples
- adds `transitions` array (between cuts)
- adds `audio_sync_beats` array (timestamps for caption emphasis)

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
- Never output anything but the JSON object."""


def build_user_message(transcripts, script, brand_config, claude_md, target_duration, name_hint):
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
    if name_hint:
        parts.append(f"# Suggested name\n{name_hint}")
    parts.append("\nProduce the edit_plan.json now. JSON only.")
    return "\n\n".join(parts)


def write_planning_brief(brief_path, transcripts, script_text, brand_config, claude_md_text, target_duration, name_hint, output_path):
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
    if name_hint:
        parts.append(f"## Suggested name\n`{name_hint}`\n")
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
    args = ap.parse_args()

    transcripts = json.loads(args.transcripts.read_text())
    brand_config = json.loads(args.brand_config.read_text())
    script_text = args.script.read_text() if args.script and args.script.exists() else None
    claude_md_text = args.claude_md.read_text() if args.claude_md and args.claude_md.exists() else None

    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    planner = args.planner or ("api" if has_key else "agent")

    if planner == "agent":
        brief_path = args.output.with_name(args.output.stem + "_brief.md")
        write_planning_brief(brief_path, transcripts, script_text, brand_config,
                             claude_md_text, args.target_duration, args.name, args.output)
        print(f"📝 Planner=agent — wrote brief to {brief_path}")
        print(f"   Next: as the Claude Code agent, read the brief and write {args.output} directly.")
        print(f"   Then run build_remotion.py --plan {args.output} ...")
        sys.exit(2)

    # planner == "api"
    if anthropic is None:
        sys.exit("❌ anthropic SDK not installed. `pip install anthropic` or use --planner=agent.")
    if not has_key:
        sys.exit("❌ ANTHROPIC_API_KEY not set. Use --planner=agent to skip the API.")

    client = anthropic.Anthropic()
    user_message = build_user_message(transcripts, script_text, brand_config, claude_md_text, args.target_duration, args.name)

    print(f"🤖 Calling {args.model} ({len(user_message)} chars)...")
    response = client.messages.create(
        model=args.model,
        max_tokens=8000,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
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
        sys.exit(f"❌ Invalid JSON: {e}\n   Saved raw to {debug_path}")

    required = {"name", "duration_target_seconds", "aspect", "fps", "v1_main", "subtitle_track"}
    missing = required - set(plan.keys())
    if missing:
        sys.exit(f"❌ Missing keys: {missing}")

    # Defaults for new Remotion-specific fields
    plan.setdefault("transitions", [])
    plan.setdefault("overlays_v2", [])
    plan.setdefault("audio_sync_beats", [])
    plan.setdefault("color_correction", {"css_filter": "saturate(0.92) contrast(1.05) brightness(1.04)"})
    plan.setdefault("render_preset", "h264_master_q18")

    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2))

    usage = response.usage
    cache_hit = getattr(usage, "cache_read_input_tokens", 0) or 0
    print(f"✅ Wrote {args.output}")
    print(f"   Tokens: in={usage.input_tokens} out={usage.output_tokens} cache_read={cache_hit}")
    print(f"   Plan: {len(plan['v1_main'])} cuts, {len(plan['subtitle_track'])} captions, "
          f"{len(plan.get('overlays_v2', []))} stats, target {plan['duration_target_seconds']}s")


if __name__ == "__main__":
    main()
