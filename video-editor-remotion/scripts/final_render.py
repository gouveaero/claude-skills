#!/usr/bin/env python3
"""
final_render.py — render the final MP4 from a Remotion project via `npx remotion render`.

Phase 9 of the Remotion-only pipeline. Replaces what export_overlays.py +
capcut_draft_builder.py used to do in the CapCut-deliverable sibling skill.

Usage:
    python3 final_render.py \\
        --remotion-dir <output>/remotion \\
        --out <output>/final.mp4 \\
        [--codec h264|h265|prores|vp8|vp9] \\
        [--crf 18] \\
        [--scale 2] \\
        [--concurrency 4] \\
        [--composition Reel] \\
        [--audio-bitrate 192k] \\
        [--props '{"hookIndex":0}']
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


CODEC_DEFAULTS = {
    # codec → (crf default, suggested extension, audio codec, suggested pixel format)
    "h264":   (18, ".mp4",  "aac", "yuv420p"),
    "h265":   (24, ".mp4",  "aac", "yuv420p"),
    "vp8":    (10, ".webm", "libopus", None),
    "vp9":    (30, ".webm", "libopus", None),
    "prores": (None, ".mov", None, "yuv422p10le"),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remotion-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path, help="Output path (e.g. final.mp4)")
    ap.add_argument("--composition", default="Reel")
    ap.add_argument("--codec", default="h264", choices=list(CODEC_DEFAULTS.keys()))
    ap.add_argument("--crf", type=int, default=None,
                    help="Constant Rate Factor (lower = better quality). Default per codec.")
    ap.add_argument("--scale", type=int, default=1,
                    help="Render scale multiplier (2 = supersample SVG for cleaner edges, costs ~3× render time)")
    ap.add_argument("--concurrency", type=int, default=None,
                    help="Parallel frame encoding (default: auto = ~half of CPU cores)")
    ap.add_argument("--audio-codec", default=None,
                    help="Override audio codec (default: aac for h264/h265, libopus for vp8/vp9)")
    ap.add_argument("--audio-bitrate", default="192k",
                    help="Audio bitrate (default: 192k)")
    ap.add_argument("--pixel-format", default=None,
                    help="Override pixel format. Default: yuv420p for h264/h265, yuv422p10le for prores.")
    ap.add_argument("--props", default=None,
                    help="JSON object passed to the composition's Zod schema (e.g. '{\"title\":\"X\"}')")
    ap.add_argument("--enforce-audio", action="store_true", default=True,
                    help="Always include audio track even if frame has none (Instagram refuses muted MP4s)")
    args = ap.parse_args()

    if shutil.which("npx") is None:
        sys.exit("npx not found — install Node.js")

    remotion_dir = args.remotion_dir.expanduser().resolve()
    if not (remotion_dir / "package.json").exists():
        sys.exit(f"Not a Remotion project: {remotion_dir} (missing package.json)")

    out_path = args.out.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    crf_default, _ext, audio_codec_default, pix_fmt_default = CODEC_DEFAULTS[args.codec]
    crf = args.crf if args.crf is not None else crf_default
    audio_codec = args.audio_codec or audio_codec_default
    pix_fmt = args.pixel_format or pix_fmt_default

    cmd: list[str] = [
        "npx", "remotion", "render",
        args.composition,
        str(out_path),
        f"--codec={args.codec}",
    ]
    if crf is not None:
        cmd.append(f"--crf={crf}")
    if args.scale > 1:
        cmd.append(f"--scale={args.scale}")
    if args.concurrency:
        cmd.append(f"--concurrency={args.concurrency}")
    if pix_fmt:
        cmd.append(f"--pixel-format={pix_fmt}")
    if audio_codec:
        cmd.append(f"--audio-codec={audio_codec}")
    if args.audio_bitrate:
        cmd.append(f"--audio-bitrate={args.audio_bitrate}")
    if args.enforce_audio:
        cmd.append("--enforce-audio-track")
    if args.props:
        cmd.append(f"--props={args.props}")

    print(f"Rendering {args.composition} -> {out_path}")
    print(f"  codec={args.codec} crf={crf} scale={args.scale} concurrency={args.concurrency or 'auto'}")
    print(f"  cmd: {' '.join(cmd)}")

    proc = subprocess.run(cmd, cwd=remotion_dir)
    if proc.returncode != 0:
        return proc.returncode

    if out_path.exists():
        size_mb = out_path.stat().st_size / 1_048_576
        print(f"\n✓ Final MP4: {out_path} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
