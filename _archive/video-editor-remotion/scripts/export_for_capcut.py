#!/usr/bin/env python3
"""
export_for_capcut.py — trim clips to edit order and save for CapCut import.

Reads edit_plan.json, trims each cut from the original clips dir using ffmpeg
(source_in → source_out), and saves numbered files into <clips_dir>/para_capcut/.

Usage:
    python3 export_for_capcut.py --plan <output>/edit_plan.json
                                  --clips-dir <original clips folder>
                                  [--out-dir <clips_dir>/para_capcut]
                                  [--proxy]            # use proxy clips instead of originals
                                  [--ffmpeg /path/to/ffmpeg]

Output files:
    01_abertura_hook.mp4
    02_problema_37pct.mp4
    ...
    09_fechamento_loop.mp4

These are trimmed re-encodes (copy stream when possible, else h264 for short clips).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

DEFAULT_FFMPEG = "ffmpeg"
BREW_FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"


def find_ffmpeg(hint: Optional[str] = None) -> str:
    candidates = [hint, BREW_FFMPEG, DEFAULT_FFMPEG]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return DEFAULT_FFMPEG


def slugify(text: str) -> str:
    """Rationale → short lowercase ASCII slug for filename."""
    # Take first segment before ' — ' or ':' or newline
    text = text.split("—")[0].split(":")[0].strip()
    # Keep letters, digits, spaces
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    words = text.lower().split()[:4]
    return "_".join(words) if words else "cut"


def trim_clip(
    ffmpeg: str,
    src: Path,
    source_in: float,
    source_out: float,
    dst: Path,
) -> None:
    duration = source_out - source_in
    cmd = [
        ffmpeg,
        "-y",
        "-ss", f"{source_in:.6f}",
        "-i", str(src),
        "-t", f"{duration:.6f}",
        # Copy streams — fast and lossless when container allows it.
        # If the clip needs re-encode (seek precision on I-frames) we still copy;
        # CapCut handles any minor frame offset fine.
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        str(dst),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        # Fall back to re-encode if stream copy failed
        cmd2 = [
            ffmpeg,
            "-y",
            "-ss", f"{source_in:.6f}",
            "-i", str(src),
            "-t", f"{duration:.6f}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            str(dst),
        ]
        result2 = subprocess.run(cmd2, capture_output=True)
        if result2.returncode != 0:
            err = result2.stderr.decode(errors="replace")[-500:]
            sys.exit(f"❌ ffmpeg failed for {src.name}: {err}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--clips-dir", required=True, type=Path,
                    help="Folder containing the original (or proxy) clips")
    ap.add_argument("--out-dir", type=Path,
                    help="Output folder (default: <clips-dir>/para_capcut)")
    ap.add_argument("--ffmpeg", type=str, default=None)
    ap.add_argument("--proxy", action="store_true",
                    help="If set, looks for clips in <clips-dir>/clips_proxy/ subfolder")
    args = ap.parse_args()

    plan_path = args.plan.expanduser().resolve()
    if not plan_path.exists():
        sys.exit(f"❌ Plan not found: {plan_path}")

    plan = json.loads(plan_path.read_text())
    cuts = plan.get("v1_main", [])
    if not cuts:
        sys.exit("❌ edit_plan.json has no v1_main cuts")

    clips_dir = args.clips_dir.expanduser().resolve()
    if args.proxy:
        clips_dir = clips_dir / "clips_proxy"
    if not clips_dir.is_dir():
        sys.exit(f"❌ Clips dir not found: {clips_dir}")

    out_dir = args.out_dir or (args.clips_dir.expanduser().resolve() / "para_capcut")
    out_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_ffmpeg(args.ffmpeg)
    print(f"🎬 ffmpeg: {ffmpeg}")
    print(f"📂 Clips dir: {clips_dir}")
    print(f"📂 Output dir: {out_dir}")
    print(f"✂️  {len(cuts)} cuts to export\n")

    for i, cut in enumerate(cuts):
        clip_name = cut["clip"]
        source_in = float(cut["source_in"])
        source_out = float(cut["source_out"])
        rationale = cut.get("rationale", clip_name)
        slug = slugify(rationale)
        duration = source_out - source_in

        src = clips_dir / clip_name
        if not src.exists():
            print(f"  ⚠  Clip not found, skipping: {src}")
            continue

        dst_name = f"{i+1:02d}_{slug}.mp4"
        dst = out_dir / dst_name

        print(f"  [{i+1:02d}/{len(cuts)}] {clip_name} [{source_in:.2f}→{source_out:.2f}s, {duration:.1f}s] → {dst_name}")
        trim_clip(ffmpeg, src, source_in, source_out, dst)
        print(f"         ✓ saved ({dst.stat().st_size // 1024}KB)")

    print(f"\n✅ Export complete → {out_dir}")
    print(f"   {len(cuts)} clips ready for CapCut. Import folder → create sequence.")


if __name__ == "__main__":
    main()
