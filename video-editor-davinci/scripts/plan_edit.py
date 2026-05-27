#!/usr/bin/env python3
"""
plan_edit.py — turns transcripts + roteiro into an edit_plan.json via Claude.

Usage:
    python3 plan_edit.py --transcripts transcripts.json [--script roteiro.md]
                         --brand-config /path/to/.video-editor.json
                         [--claude-md /path/to/CLAUDE.md]
                         --output edit_plan.json
                         [--target-duration 30]
                         [--model claude-sonnet-4-6]

Output JSON shape — see references/edit-plan-schema.md.

Uses prompt caching: the system prompt + brand config + claude.md go to cache
(rarely change), only the transcripts + script vary per call.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an expert short-form video editor specializing in vertical Reels/TikToks/Shorts. You produce machine-readable edit plans that drive DaVinci Resolve via scripting.

# Your job

Given: raw clip transcriptions (word-level timestamps) + a roteiro (script, optional) + brand config + project rules.

Output: a single JSON object that describes the final timeline edit. NOTHING ELSE — no preamble, no markdown fences, no explanations. Just the JSON.

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
  "subtitle_track": [
    {
      "text": "<UPPERCASE 1-4 words max per entry>",
      "start": <seconds in final timeline>,
      "end": <seconds in final timeline>,
      "style": "highlight_accent" | "highlight_box" | "minimal"
    }
  ],
  "overlays_v2": [],
  "audio_ducking": [],
  "render_preset": "h264_master_q18"
}

# Editing principles

1. **Aggressive cutting**: clips on V1 should be 1-4s each. Cut filler ("é...", "tipo", "então..."), repeated takes, breath pauses. Pick THE best take of each beat.
2. **Caption density**: 1-3 words per subtitle entry, max 4. Group words by natural breath/emphasis. Total caption coverage ≈ 90% of speech.
3. **CAPS for captions**: text field always UPPERCASE.
4. **Subtitle timing**: align to word_timestamps from transcripts — start when the word starts, end ~50ms after last word.
5. **Source IN/OUT precision**: use the word_timestamps to find clean cut points (silence between words). Don't cut mid-word.
6. **Timeline_start**: must be sequential, no gaps unless intentional. Compute as cumulative duration.
7. **Brand voice**: respect brand config (caption style, colors implicit). Respect CLAUDE.md compliance rules (e.g., OAB rules for legal content — no guarantees, no promises).

# Forbidden

- Never invent clips that aren't in the transcripts.
- Never produce timeline gaps (timeline_start[i+1] must equal timeline_start[i] + (source_out[i] - source_in[i])).
- Never exceed duration_target_seconds by more than 10%.
- Never output anything but the JSON object."""


def build_user_message(
    transcripts: dict,
    script: str | None,
    brand_config: dict,
    claude_md: str | None,
    target_duration: float,
    name_hint: str | None,
) -> str:
    parts = []

    parts.append("# Brand config\n```json\n" + json.dumps(brand_config, ensure_ascii=False, indent=2) + "\n```")

    if claude_md:
        parts.append("# Project CLAUDE.md (compliance rules + voice)\n" + claude_md.strip())

    if script:
        parts.append("# Roteiro\n" + script.strip())
    else:
        parts.append("# Roteiro\n(no script provided — infer narrative from transcripts)")

    # Compact transcripts: keep words but drop probabilities to save tokens
    compact = {
        "language": transcripts.get("language"),
        "clips": {
            name: {
                "duration": clip.get("duration"),
                "text": clip.get("text"),
                "words": [
                    {"w": w["word"], "s": w["start"], "e": w["end"]}
                    for w in clip.get("words", [])
                ],
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcripts", required=True, type=Path)
    ap.add_argument("--script", type=Path, help="Path to roteiro.md (optional)")
    ap.add_argument("--brand-config", required=True, type=Path)
    ap.add_argument("--claude-md", type=Path, help="Path to project CLAUDE.md (optional)")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--target-duration", type=float, default=30.0)
    ap.add_argument("--name", help="Suggested kebab-case name for the reel")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    transcripts = json.loads(args.transcripts.read_text())
    brand_config = json.loads(args.brand_config.read_text())
    script_text = args.script.read_text() if args.script and args.script.exists() else None
    claude_md_text = args.claude_md.read_text() if args.claude_md and args.claude_md.exists() else None

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("❌ ANTHROPIC_API_KEY not set in environment.")

    client = anthropic.Anthropic()

    user_message = build_user_message(
        transcripts, script_text, brand_config, claude_md_text,
        args.target_duration, args.name,
    )

    print(f"🤖 Calling {args.model} ({len(user_message)} chars input)...")
    response = client.messages.create(
        model=args.model,
        max_tokens=8000,
        system=[
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    # Strip code fences if model added them
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
        sys.exit(f"❌ Claude returned invalid JSON: {e}\n   Raw output saved to {debug_path}")

    # Light validation
    required_keys = {"name", "duration_target_seconds", "aspect", "fps", "v1_main", "subtitle_track"}
    missing = required_keys - set(plan.keys())
    if missing:
        sys.exit(f"❌ Plan is missing required keys: {missing}")

    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2))

    usage = response.usage
    cache_hit = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_create = getattr(usage, "cache_creation_input_tokens", 0) or 0
    print(f"✅ Wrote {args.output}")
    print(f"   Tokens: in={usage.input_tokens} out={usage.output_tokens} "
          f"cache_read={cache_hit} cache_create={cache_create}")
    print(f"   Plan: {len(plan['v1_main'])} cuts, "
          f"{len(plan['subtitle_track'])} captions, "
          f"target {plan['duration_target_seconds']}s")


if __name__ == "__main__":
    main()
