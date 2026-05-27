#!/usr/bin/env python3
"""
build_reel.py — top-level orchestrator: clips + roteiro → Remotion project (+ optional render).

Usage:
    python3 build_reel.py --input <clips_dir> [--script <roteiro.md>]
                          [--name <reel-name>] [--target-duration 30]
                          [--language pt]
                          [--render | --render-only]
                          [--no-preview] [--no-open]
                          [--skip-setup --skip-transcribe --skip-plan --skip-build]

Pipeline (in order):
1. Find <ClientFolder>/.video-editor.json (walks up from --input)
2. setup_project.py     — transcode + scaffold Remotion (idempotent)
3. transcribe.py        — mlx-whisper → transcripts.json (cached)
4. plan_edit.py         — Claude API → edit_plan.json
5. build_remotion.py    — generate Root.tsx + Reel.tsx + components
6. preview.py           — launch Studio + open browser  (skip with --no-preview)
7. render.py            — final MP4                      (only with --render or --render-only)

Each phase is skippable; --render-only runs only step 7 (assumes 1-5 already done).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def find_brand_config(start: Path) -> tuple[Path | None, Path | None]:
    cur = start.resolve()
    while cur != cur.parent:
        candidate = cur / ".video-editor.json"
        if candidate.exists():
            return candidate, cur
        cur = cur.parent
    return None, None


def find_claude_md(client_root: Path) -> Path | None:
    p = client_root / "CLAUDE.md"
    return p if p.exists() else None


def run_phase(label: str, cmd: list, env=None, allow_exit2: bool = False) -> int:
    print(f"\n━━━ {label} ━━━")
    print("  $ " + " ".join(str(x) for x in cmd))
    result = subprocess.run(cmd, env=env)
    if result.returncode == 2 and allow_exit2:
        return 2
    if result.returncode != 0:
        sys.exit(f"❌ {label} failed (exit {result.returncode})")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--script", type=Path)
    ap.add_argument("--name")
    ap.add_argument("--brand-config", type=Path,
                    help="Override .video-editor.json path (skip walk-up)")
    ap.add_argument("--client-root", type=Path,
                    help="Override client root for output dir (defaults to brand-config's parent)")
    ap.add_argument("--target-duration", type=float, default=30.0)
    ap.add_argument("--language", default="pt")
    ap.add_argument("--whisper-model", default="mlx-community/whisper-large-v3-mlx")
    ap.add_argument("--llm-model", default="claude-sonnet-4-6")
    ap.add_argument("--planner", choices=["api", "agent"], default=None,
                    help="api: call Anthropic SDK. agent: write planning brief and "
                         "stop, expecting the calling Claude Code agent to write "
                         "edit_plan.json by hand. Default: api if ANTHROPIC_API_KEY is set, else agent.")
    ap.add_argument("--proxy-resolution", type=int, default=1080)
    ap.add_argument("--force-transcribe", action="store_true")
    ap.add_argument("--skip-setup", action="store_true")
    ap.add_argument("--skip-transcribe", action="store_true")
    ap.add_argument("--skip-plan", action="store_true")
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--no-preview", action="store_true",
                    help="Don't launch Remotion Studio at the end")
    ap.add_argument("--no-open", action="store_true",
                    help="Don't open browser when previewing")
    ap.add_argument("--render", action="store_true", help="Render MP4 after build")
    ap.add_argument("--render-only", action="store_true",
                    help="Only render (assumes everything else already done)")
    ap.add_argument("--hq", action="store_true", help="High-quality render (prores 4K)")
    args = ap.parse_args()

    input_dir: Path = args.input.expanduser().resolve()
    if not input_dir.is_dir():
        sys.exit(f"❌ Input not a dir: {input_dir}")

    name = args.name or input_dir.name.replace(" ", "_").lower()
    if args.brand_config:
        brand_config_path = args.brand_config.expanduser().resolve()
        if not brand_config_path.exists():
            sys.exit(f"❌ --brand-config path doesn't exist: {brand_config_path}")
        client_root = (args.client_root.expanduser().resolve()
                       if args.client_root else brand_config_path.parent)
    else:
        brand_config_path, client_root = find_brand_config(input_dir)
        if not brand_config_path:
            sys.exit(
                f"❌ No .video-editor.json found walking up from {input_dir}. "
                "Pass --brand-config explicitly."
            )
    print(f"📋 Brand config: {brand_config_path}")
    print(f"📂 Client root: {client_root}")
    output_dir = client_root / "output" / name
    output_dir.mkdir(parents=True, exist_ok=True)
    remotion_dir = output_dir / "remotion"
    transcripts_path = output_dir / "transcripts.json"
    plan_path = output_dir / "edit_plan.json"

    script_path = args.script
    if script_path is None:
        candidate = input_dir / "roteiro.md"
        if candidate.exists():
            script_path = candidate
            print(f"📝 Auto-detected roteiro: {script_path}")
    claude_md = find_claude_md(client_root)
    if claude_md:
        print(f"📜 CLAUDE.md: {claude_md}")

    # Render-only short-circuit
    if args.render_only:
        out_mp4 = output_dir / "final.mp4"
        cmd = [
            sys.executable, str(SCRIPT_DIR / "render.py"),
            "--remotion-dir", str(remotion_dir),
            "--out", str(out_mp4),
        ]
        if args.hq:
            cmd.append("--hq")
        run_phase("Render only", cmd)
        return

    # Phase 1: Setup project
    if not args.skip_setup:
        cmd = [
            sys.executable, str(SCRIPT_DIR / "setup_project.py"),
            "--input", str(input_dir),
            "--name", name,
            "--brand-config", str(brand_config_path),
            "--proxy-resolution", str(args.proxy_resolution),
        ]
        run_phase("Phase 1/5: Setup project", cmd)

    # Phase 2: Transcribe
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
        run_phase("Phase 2/5: Transcribe", cmd)
    elif not transcripts_path.exists():
        sys.exit(f"❌ --skip-transcribe but {transcripts_path} doesn't exist")

    # Phase 3: Plan edit
    if not args.skip_plan:
        planner = args.planner or ("api" if os.environ.get("ANTHROPIC_API_KEY") else "agent")
        cmd = [
            sys.executable, str(SCRIPT_DIR / "plan_edit.py"),
            "--transcripts", str(transcripts_path),
            "--brand-config", str(brand_config_path),
            "--output", str(plan_path),
            "--target-duration", str(args.target_duration),
            "--name", name,
            "--model", args.llm_model,
            "--planner", planner,
        ]
        if script_path:
            cmd += ["--script", str(script_path)]
        if claude_md:
            cmd += ["--claude-md", str(claude_md)]
        rc = run_phase("Phase 3/5: Plan edit", cmd, allow_exit2=True)
        if rc == 2:
            print("\n⏸  Pipeline paused — planner=agent wrote a brief next to the plan path.")
            print(f"   As the Claude Code agent, write {plan_path} now, then re-run this command")
            print(f"   with --skip-plan to continue with build/preview/render.")
            sys.exit(0)
    elif not plan_path.exists():
        sys.exit(f"❌ --skip-plan but {plan_path} doesn't exist")

    # Phase 4: Build Remotion
    if not args.skip_build:
        cmd = [
            sys.executable, str(SCRIPT_DIR / "build_remotion.py"),
            "--plan", str(plan_path),
            "--remotion-dir", str(remotion_dir),
            "--brand-config", str(brand_config_path),
        ]
        run_phase("Phase 4/5: Build Remotion (Root.tsx + Reel.tsx + components)", cmd)

    plan = json.loads(plan_path.read_text())
    print(f"\n✅ Build complete. Output: {output_dir}")
    print(f"   Plan: {len(plan['v1_main'])} cuts, "
          f"{len(plan.get('subtitle_track', []))} captions, "
          f"{len(plan.get('overlays_v2', []))} stats, "
          f"~{plan.get('duration_target_seconds', '?')}s")

    # Phase 5: Render (optional)
    if args.render:
        out_mp4 = output_dir / "final.mp4"
        cmd = [
            sys.executable, str(SCRIPT_DIR / "render.py"),
            "--remotion-dir", str(remotion_dir),
            "--out", str(out_mp4),
        ]
        if args.hq:
            cmd.append("--hq")
        run_phase("Phase 5/5: Render MP4", cmd)

    # Preview (default: yes)
    if not args.no_preview:
        cmd = [
            sys.executable, str(SCRIPT_DIR / "preview.py"),
            "--remotion-dir", str(remotion_dir),
        ]
        if args.no_open:
            cmd.append("--no-open")
        # preview.py blocks (Studio is foreground)
        run_phase("Preview: Remotion Studio", cmd)


if __name__ == "__main__":
    main()
