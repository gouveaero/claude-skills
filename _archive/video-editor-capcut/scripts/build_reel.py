#!/usr/bin/env python3
"""
build_reel.py — orquestrador da skill video-editor-capcut

Pipeline:
  1. setup_project.py  — transcode HEVC→H.264, scaffold output dir
  2. transcribe.py     — mlx-whisper word-level (cached)
  3. plan_edit.py      — Claude API → edit_plan.json
  4. capcut_draft_builder.py — edit_plan.json → CapCut draft
  5. open CapCut (opcional)

Uso:
  python3 build_reel.py \
    --input "/path/to/clips" \
    --name "reel_tribotax_01" \
    --brand-config "/path/to/client/.video-editor.json" \
    [--target-duration 30] \
    [--roteiro "/path/to/roteiro.md"] \
    [--skip-transcode] \
    [--skip-transcribe] \
    [--skip-plan] \
    [--open]
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS   = SKILL_DIR / "scripts"


def run(cmd: list, check=True, **kwargs):
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=check, **kwargs)


def main():
    parser = argparse.ArgumentParser(description="CapCut reel pipeline")
    parser.add_argument("--input",          required=True,  help="Folder with raw clips")
    parser.add_argument("--name",           required=True,  help="Reel/draft name (no spaces)")
    parser.add_argument("--brand-config",   required=True,  help="Path to .video-editor.json")
    parser.add_argument("--target-duration",default=30,     type=int, help="Target duration in seconds")
    parser.add_argument("--roteiro",        default=None,   help="Optional roteiro .md for plan_edit context")
    parser.add_argument("--skip-transcode", action="store_true")
    parser.add_argument("--skip-transcribe",action="store_true")
    parser.add_argument("--skip-plan",      action="store_true")
    parser.add_argument("--draft-root",     default=None,   help="Override CapCut projects folder")
    parser.add_argument("--open",           action="store_true", help="Launch CapCut after writing")
    args = parser.parse_args()

    input_dir    = Path(args.input).resolve()
    brand_config = Path(args.brand_config).resolve()

    if not input_dir.exists():
        print(f"ERROR: input dir not found: {input_dir}")
        sys.exit(1)
    if not brand_config.exists():
        print(f"ERROR: brand config not found: {brand_config}")
        sys.exit(1)

    # Output dir: sibling of input dir named after reel
    output_dir = input_dir.parent / args.name
    output_dir.mkdir(exist_ok=True)

    clips_proxy  = output_dir / "clips_proxy"
    transcripts  = output_dir / "transcripts.json"
    edit_plan    = output_dir / "edit_plan.json"

    print(f"\n{'='*60}")
    print(f"  video-editor-capcut pipeline")
    print(f"  Input : {input_dir}")
    print(f"  Output: {output_dir}")
    print(f"  Draft : {args.name}")
    print(f"{'='*60}")

    # ── STEP 1: setup / transcode ─────────────────────────────────────────────
    if not args.skip_transcode:
        run([sys.executable, SCRIPTS / "setup_project.py",
             "--input", str(input_dir),
             "--output", str(output_dir),
             "--name", args.name])
    else:
        clips_proxy.mkdir(exist_ok=True)
        print("[skip] transcode")

    # ── STEP 2: transcribe ────────────────────────────────────────────────────
    if not args.skip_transcribe:
        run([sys.executable, SCRIPTS / "transcribe.py",
             "--input", str(clips_proxy),
             "--output", str(transcripts),
             "--brand-config", str(brand_config)])
    else:
        print("[skip] transcribe")

    # ── STEP 3: plan edit ─────────────────────────────────────────────────────
    if not args.skip_plan:
        plan_cmd = [
            sys.executable, SCRIPTS / "plan_edit.py",
            "--transcripts", str(transcripts),
            "--brand-config", str(brand_config),
            "--output", str(edit_plan),
            "--target-duration", str(args.target_duration),
            "--clips-dir", str(clips_proxy),
        ]
        if args.roteiro:
            plan_cmd += ["--roteiro", args.roteiro]
        result = run(plan_cmd, check=False)

        # plan_edit exits 2 when running in agent mode (no ANTHROPIC_API_KEY)
        if result.returncode == 2:
            print("\n[plan_edit] Agent mode: edit_plan.json not yet written.")
            print("  → Claude Code deve ler o brief em:", output_dir / f"{args.name}_brief.md")
            print("  → Escrever edit_plan.json e depois rodar com --skip-plan")
            sys.exit(2)
        elif result.returncode != 0:
            print(f"ERROR: plan_edit.py failed (exit {result.returncode})")
            sys.exit(result.returncode)
    else:
        print("[skip] plan_edit")

    if not edit_plan.exists():
        print(f"ERROR: edit_plan.json not found at {edit_plan}")
        sys.exit(1)

    # ── STEP 4: build CapCut draft ────────────────────────────────────────────
    builder_cmd = [
        sys.executable, SCRIPTS / "capcut_draft_builder.py",
        "--plan",       str(edit_plan),
        "--clips-dir",  str(clips_proxy),
        "--draft-name", args.name,
    ]
    if args.draft_root:
        builder_cmd += ["--draft-root", args.draft_root]
    if args.open:
        builder_cmd.append("--open")

    run(builder_cmd)

    print(f"\n{'='*60}")
    print(f"  Pipeline concluída!")
    print(f"  Projeto '{args.name}' disponível no CapCut Desktop.")
    print(f"  Abra o CapCut → aba Rascunhos → '{args.name}'")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
