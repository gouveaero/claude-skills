#!/usr/bin/env python3
"""
render.py — renders a Remotion composition to MP4 (or other formats).

Usage:
    python3 render.py --remotion-dir <output>/remotion --out <output>/final.mp4
                      [--composition Reel] [--codec h264|h265|vp9|prores]
                      [--crf 18] [--scale 1] [--concurrency 4]
                      [--hq]                # shortcut: prores 4444, scale 2
                      [--alpha]             # ProRes 4444 with alpha for overlay clips
                      [--props '{"foo": "bar"}']

Wraps `npx remotion render` with sensible defaults. Tries to leverage all CPU
cores via --concurrency. The composition must be registered in src/Root.tsx.

ALPHA RENDERING (overlay graphics with transparency):
  Use --alpha to produce a ProRes 4444 .mov with a transparent background.
  Requirements:
    1. Composition's root element must NOT set backgroundColor (or set it to
       "transparent"). E.g. <AbsoluteFill> without a backgroundColor prop.
    2. Avoid heavy WebkitTextStroke / drop-shadow in dark colors — they look
       like a halo when composited over video. Prefer no stroke, or use a
       stroke color matching the brand accent (not near-black).
  Output: ProRes 4444 .mov (~5-15 MB/s) with yuva444p10le pixel format.
  CapCut imports these directly with alpha; no blend mode needed.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remotion-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--composition", default="Reel")
    ap.add_argument("--codec", default="h264", choices=["h264", "h265", "vp9", "prores"])
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--scale", type=float, default=1.0, help="Scale factor (2 = 4K from 1080p)")
    ap.add_argument("--concurrency", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--hq", action="store_true",
                    help="Shortcut for high quality: --codec prores --scale 2 --crf 14")
    ap.add_argument("--alpha", action="store_true",
                    help="ProRes 4444 + yuva444p10le + PNG image format for alpha-channel overlays")
    ap.add_argument("--props", help="JSON string of input props for the composition")
    args = ap.parse_args()

    remotion_dir = args.remotion_dir.expanduser().resolve()
    if not (remotion_dir / "package.json").exists():
        sys.exit(f"❌ {remotion_dir}/package.json missing — run setup_project.py first")

    out_path = args.out.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    codec = args.codec
    crf = args.crf
    scale = args.scale
    if args.hq:
        codec = "prores"
        scale = 2.0
        crf = 14
    if args.alpha:
        # ProRes 4444 is the only codec we use that supports alpha cleanly
        codec = "prores"

    cmd = [
        "npx", "remotion", "render",
        args.composition,
        str(out_path),
        f"--codec={codec}",
        f"--concurrency={args.concurrency}",
        f"--scale={scale}",
    ]
    # CRF only applies to lossy codecs
    if codec in {"h264", "h265", "vp9"}:
        cmd.append(f"--crf={crf}")
    if codec == "prores":
        cmd.append("--prores-profile=4444")
    if args.alpha:
        # PNG image format + yuva pixel format are both required for alpha output.
        # Without --image-format=png Remotion writes JPEG frames and the alpha
        # channel is silently dropped.
        cmd.append("--pixel-format=yuva444p10le")
        cmd.append("--image-format=png")

    if args.props:
        # Validate JSON before passing to Remotion
        try:
            json.loads(args.props)
        except json.JSONDecodeError as e:
            sys.exit(f"❌ --props isn't valid JSON: {e}")
        cmd.append(f"--props={args.props}")

    print(f"🎬 Rendering {args.composition} → {out_path}")
    print(f"   $ {' '.join(cmd)}")
    print(f"   cwd: {remotion_dir}")

    result = subprocess.run(cmd, cwd=remotion_dir)
    if result.returncode != 0:
        sys.exit(f"❌ Render failed (exit {result.returncode})")

    if not out_path.exists():
        sys.exit(f"❌ Render reported success but {out_path} not found")
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Wrote {out_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
