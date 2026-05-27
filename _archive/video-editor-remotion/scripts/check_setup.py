#!/usr/bin/env python3
"""
check_setup.py — validates prerequisites for video-editor-remotion skill.

Checks:
- Node.js >= 18
- npx available
- ffmpeg + ffprobe installed
- mlx-whisper python package (Apple Silicon) OR whisper.cpp fallback
- ANTHROPIC_API_KEY env var set
- anthropic Python package available

Usage:
    python3 check_setup.py
    python3 check_setup.py --quiet   # only print failures
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def ok(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(f"  {GREEN}✓{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


def check_node() -> bool:
    if not shutil.which("node"):
        fail("node not found. Install via https://nodejs.org or `brew install node`")
        return False
    try:
        out = subprocess.check_output(["node", "--version"], text=True).strip()
        version = out.lstrip("v").split(".")[0]
        if int(version) < 18:
            fail(f"node {out} is too old. Need v18+ (Remotion requirement)")
            return False
        ok(f"node {out}")
        return True
    except Exception as e:
        fail(f"node version check failed: {e}")
        return False


def check_npx() -> bool:
    if not shutil.which("npx"):
        fail("npx not found. Comes with node — reinstall node.")
        return False
    ok("npx available")
    return True


def check_ffmpeg() -> bool:
    ok_count = 0
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool):
            ok(f"{tool} available")
            ok_count += 1
        else:
            fail(f"{tool} not found. Install: `brew install ffmpeg`")
    return ok_count == 2


def check_whisper() -> bool:
    """mlx-whisper preferred on Apple Silicon, whisper.cpp fallback."""
    try:
        import mlx_whisper  # noqa: F401
        ok("mlx-whisper installed (Apple Silicon)")
        return True
    except ImportError:
        pass
    if shutil.which("whisper-cli") or shutil.which("main"):
        ok("whisper.cpp binary detected")
        return True
    warn(
        "Nenhum whisper encontrado. Instale: `pip install mlx-whisper` (Apple Silicon) "
        "ou `npx remotion install whisper-cpp` (cross-platform)."
    )
    return False


def check_anthropic_key() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY"):
        ok("ANTHROPIC_API_KEY set (planner=api default)")
        return True
    warn(
        "ANTHROPIC_API_KEY not in env. plan_edit will fall back to --planner=agent "
        "(the calling Claude Code agent writes edit_plan.json directly — no API call). "
        "If you want SDK mode, add to ~/.zshrc: `export ANTHROPIC_API_KEY=sk-ant-...`"
    )
    return True  # not a hard failure anymore


def check_anthropic_pkg() -> bool:
    try:
        import anthropic  # noqa: F401
        ok("anthropic Python package installed")
        return True
    except ImportError:
        warn("anthropic package missing — only needed for --planner=api. "
             "Install with `pip install anthropic` if you want SDK mode.")
        return True  # soft warning; agent mode works without it


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    print("🎬 video-editor-remotion — setup check\n")
    results = [
        check_node(),
        check_npx(),
        check_ffmpeg(),
        check_whisper(),
        check_anthropic_key(),
        check_anthropic_pkg(),
    ]

    failed = sum(1 for r in results if not r)
    print()
    if failed == 0:
        print(f"{GREEN}✅ All checks passed. Ready to build reels.{RESET}")
        return 0
    print(f"{RED}❌ {failed} check(s) failed. See above.{RESET}")
    print(f"   Reference: ~/.claude/skills/video-editor-remotion/references/setup.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
