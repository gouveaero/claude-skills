#!/usr/bin/env python3
"""
build_reel.py — end-to-end orchestrator: clips + roteiro → DaVinci timeline.

Usage:
    python3 build_reel.py --input <clips_dir> [--script <roteiro.md>]
                          [--name <reel-name>]
                          [--target-duration 30]
                          [--language pt]

What it does (in order):
1. Finds <ClientFolder>/.video-editor.json (walks up from --input)
2. Runs scripts/transcribe.py if transcripts.json doesn't exist (or --force)
3. Runs scripts/plan_edit.py to produce edit_plan.json
4. Runs scripts/build_timeline.py to drive Resolve

Each phase writes to <ClientFolder>/output/<name>/.
Skip a phase that's already done by passing --skip-transcribe / --skip-plan.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()


def find_brand_config(start: Path) -> tuple[Path | None, Path | None]:
    """Walk up from `start` to find .video-editor.json. Returns (config_path, client_root)."""
    current = start.resolve()
    while current != current.parent:
        candidate = current / ".video-editor.json"
        if candidate.exists():
            return candidate, current
        current = current.parent
    return None, None


def find_claude_md(client_root: Path) -> Path | None:
    p = client_root / "CLAUDE.md"
    return p if p.exists() else None


def run_phase(label: str, cmd: list[str]) -> None:
    print(f"\n━━━ {label} ━━━")
    print("  $ " + " ".join(str(x) for x in cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"❌ {label} failed (exit {result.returncode})")


def run_montage(args, input_dir: Path, name: str) -> None:
    """Visual-driven montage path: analyze_visual → plan_montage → build_timeline.
    Bypasses transcribe/plan_edit entirely — those are speech-driven and don't
    apply to a B-roll montage with no narration to cut around."""
    brand_config_path, client_root = find_brand_config(input_dir)
    if brand_config_path:
        print(f"📋 Brand config: {brand_config_path}")
        print(f"📂 Client root: {client_root}")
        output_dir = client_root / "output" / name
    else:
        # Montage mode doesn't need brand captions/compliance rules — don't
        # force a .video-editor.json to exist just to pick a project folder.
        print("📋 No .video-editor.json found — proceeding without one (montage mode)")
        output_dir = input_dir / "output" / name
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates_path = output_dir / "visual_candidates.json"
    plan_path = output_dir / "edit_plan.json"

    if not args.skip_transcribe:  # reused flag name: skip the analyze phase
        cmd = [
            sys.executable, str(SCRIPT_DIR / "analyze_visual.py"),
            "--input", str(input_dir),
            "--output", str(candidates_path),
        ]
        if args.only:
            cmd.extend(["--only", args.only])
        if args.vision:
            cmd.append("--vision")
        run_phase("Phase 1/3: Analyze visual", cmd)
    elif not candidates_path.exists():
        sys.exit(f"❌ --skip-transcribe but {candidates_path} doesn't exist")

    if not args.skip_plan:
        cmd = [
            sys.executable, str(SCRIPT_DIR / "plan_montage.py"),
            "--candidates", str(candidates_path),
            "--target-duration", str(args.target_duration),
            "--name", name,
            "--output", str(plan_path),
        ]
        if args.music:
            cmd.extend(["--music", str(args.music)])
        if args.no_speed:
            cmd.append("--no-speed")
        if args.vision:  # only meaningful alongside --vision candidates
            cmd.append("--reorder")
        if args.max_per_tag is not None:
            cmd.extend(["--max-per-tag", str(args.max_per_tag)])
        run_phase("Phase 2/3: Plan montage", cmd)
    elif not plan_path.exists():
        sys.exit(f"❌ --skip-plan but {plan_path} doesn't exist")

    if not args.skip_build:
        cmd = [
            sys.executable, str(SCRIPT_DIR / "build_timeline.py"),
            "--plan", str(plan_path),
            "--clips-dir", str(input_dir),
            "--project-name", name,
        ]
        if brand_config_path:
            cmd.extend(["--brand-config", str(brand_config_path)])
        run_phase("Phase 3/3: Build timeline (DaVinci)", cmd)

    plan = json.loads(plan_path.read_text())
    print(f"\n✅ Done. Output: {output_dir}")
    print(f"   Project '{name}' is in DaVinci Resolve Project Manager")
    print(f"   Plan: {len(plan['v1_main'])} shots, ~{plan['duration_target_seconds']}s"
          f"{' + music' if plan.get('music') else ''}")
    print(f"\n   To iterate: edit {plan_path} and re-run with --skip-transcribe --skip-plan")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path, help="Directory with clips")
    ap.add_argument("--script", type=Path, help="Path to roteiro.md (default: <input>/roteiro.md if exists)")
    ap.add_argument("--name", help="Reel name (kebab-case). Default: input dir name")
    ap.add_argument("--target-duration", type=float, default=30.0)
    ap.add_argument("--language", default="pt")
    ap.add_argument("--whisper-model", default="mlx-community/whisper-large-v3-mlx")
    ap.add_argument("--llm-model", default="claude-sonnet-4-6")
    ap.add_argument("--force-transcribe", action="store_true",
                    help="Re-transcribe clips even if cache exists")
    ap.add_argument("--skip-transcribe", action="store_true")
    ap.add_argument("--skip-plan", action="store_true")
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--montage", action="store_true",
                    help="Visual-driven montage mode (no speech/roteiro) — analyze_visual + plan_montage instead of transcribe + plan_edit")
    ap.add_argument("--music", type=Path, help="[--montage] Music bed (.mp3/.wav) to beat-sync cuts to")
    ap.add_argument("--vision", action="store_true", help="[--montage] Enable Claude Vision shot scoring + LLM reorder")
    ap.add_argument("--no-speed", action="store_true", help="[--montage] Skip speed-ramp hero shots")
    ap.add_argument("--only", help="[--montage] Restrict analysis to a single clip filename (smoke test)")
    ap.add_argument("--max-per-tag", type=int, help="[--montage] Cap selected shots sharing any one tag (diversity)")
    args = ap.parse_args()

    input_dir: Path = args.input.expanduser().resolve()
    if not input_dir.is_dir():
        sys.exit(f"❌ Input dir not found: {input_dir}")

    name = args.name or input_dir.name.replace(" ", "_").lower()

    if args.montage:
        run_montage(args, input_dir, name)
        return

    brand_config_path, client_root = find_brand_config(input_dir)
    if not brand_config_path:
        sys.exit(
            f"❌ No .video-editor.json found walking up from {input_dir}. "
            "Create one or copy brand-configs/_example.json from the skill."
        )
    print(f"📋 Brand config: {brand_config_path}")
    print(f"📂 Client root: {client_root}")

    output_dir = client_root / "output" / name
    output_dir.mkdir(parents=True, exist_ok=True)

    transcripts_path = output_dir / "transcripts.json"
    plan_path = output_dir / "edit_plan.json"

    # Resolve script path
    script_path = args.script
    if script_path is None:
        candidate = input_dir / "roteiro.md"
        if candidate.exists():
            script_path = candidate
            print(f"📝 Auto-detected roteiro: {script_path}")

    claude_md = find_claude_md(client_root)
    if claude_md:
        print(f"📜 CLAUDE.md: {claude_md}")

    # Phase 1: transcribe
    if not args.skip_transcribe:
        cmd = [
            sys.executable, str(SCRIPT_DIR / "transcribe.py"),
            "--input", str(input_dir),
            "--output", str(transcripts_path),
            "--model", args.whisper_model,
            "--language", args.language,
        ]
        if args.force_transcribe:
            cmd.append("--force")
        run_phase("Phase 1/3: Transcribe", cmd)
    elif not transcripts_path.exists():
        sys.exit(f"❌ --skip-transcribe but {transcripts_path} doesn't exist")

    # Phase 2: plan_edit
    if not args.skip_plan:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("❌ ANTHROPIC_API_KEY env var required for plan_edit phase. Set it or use --skip-plan.")
        cmd = [
            sys.executable, str(SCRIPT_DIR / "plan_edit.py"),
            "--transcripts", str(transcripts_path),
            "--brand-config", str(brand_config_path),
            "--output", str(plan_path),
            "--target-duration", str(args.target_duration),
            "--name", name,
            "--model", args.llm_model,
        ]
        if script_path:
            cmd.extend(["--script", str(script_path)])
        if claude_md:
            cmd.extend(["--claude-md", str(claude_md)])
        run_phase("Phase 2/3: Plan edit (Claude)", cmd)
    elif not plan_path.exists():
        sys.exit(f"❌ --skip-plan but {plan_path} doesn't exist")

    # Phase 3: build timeline
    if not args.skip_build:
        cmd = [
            sys.executable, str(SCRIPT_DIR / "build_timeline.py"),
            "--plan", str(plan_path),
            "--clips-dir", str(input_dir),
            "--brand-config", str(brand_config_path),
            "--project-name", name,
        ]
        run_phase("Phase 3/3: Build timeline (DaVinci)", cmd)

    plan = json.loads(plan_path.read_text())
    print(f"\n✅ Done. Output: {output_dir}")
    print(f"   Project '{name}' is in DaVinci Resolve Project Manager")
    print(f"   Plan: {len(plan['v1_main'])} cuts, "
          f"{len(plan['subtitle_track'])} captions, "
          f"~{plan['duration_target_seconds']}s")
    print(f"\n   To iterate: edit {plan_path} and re-run with --skip-transcribe --skip-plan")


if __name__ == "__main__":
    main()
