#!/usr/bin/env python3
"""
color_grade_batch.py — apply a cinematic color preset to clips and re-encode.

Two modes:
  --mode samples    Take ONE clip (or a trimmed slice), render all presets side-by-side
                    so you can pick the look. Outputs to <input_dir>/samples_color/.
  --mode batch      Render ALL clips in a folder with a chosen preset.

Source assumed to be 10-bit HEVC BT.2020 (phone "HDR" / HLG). Converts to
Rec.709 SDR via zscale + Hable tonemap before applying the preset.

Presets:
  - cinematic_warm   warm highlights, slight cool shadows, +sat (matches earth-tone brands)
  - teal_orange      classic blockbuster, strong teal/orange split
  - filmic_neutral   Kodak-ish, subtle, less aggressive
  - baseline         just BT.2020 → Rec.709, no grade (for comparison)

Usage:
  # Sample mode — render 8s of one clip in all presets:
  python3 color_grade_batch.py --mode samples \\
      --sample-clip "20260505_174342.mp4" \\
      --sample-duration 8 \\
      --input "/Users/gabriel/Downloads/Video 01 Alex"

  # Batch mode — render all clips with chosen preset:
  python3 color_grade_batch.py --mode batch \\
      --preset cinematic_warm \\
      --input "/Users/gabriel/Downloads/Video 01 Alex" \\
      --output "/Users/gabriel/Downloads/Video 01 Alex_graded"
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Prefer ffmpeg-full (has libzimg/zscale + libplacebo for HLG tonemap).
# Fall back to plain ffmpeg, but HLG sources won't render cleanly.
_FFMPEG_FULL = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
_FFPROBE_FULL = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
FFMPEG = _FFMPEG_FULL if Path(_FFMPEG_FULL).exists() else (shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg")
FFPROBE = _FFPROBE_FULL if Path(_FFPROBE_FULL).exists() else (shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe")

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv"}

# Phone "10-bit HDR" sources are HLG (arib-std-b67) on BT.2020 NC primaries.
# Hable with npl=100 gives correct exposure (highlights preserved, no blowout).
# The "washed" look comes from the post-grade being too subtle — fixed below
# with much more aggressive contrast/saturation/curves.
TONEMAP_CHAIN = (
    "zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:"
        "t=linear:npl=100,"
    "format=gbrpf32le,"
    "zscale=p=bt709,"
    "tonemap=hable:desat=2.0,"
    "zscale=t=bt709:m=bt709:r=tv,"
    "format=yuv420p"
)


def _grade_filter(preset: str) -> str:
    """Return the post-tonemap grade filter chain for a preset."""
    if preset == "baseline":
        return ""  # tonemap only

    if preset == "cinematic_warm":
        # AGGRESSIVE warm look: strong contrast, +50% sat, copper highlights, deep shadows
        return (
            "eq=contrast=1.32:saturation=1.50:gamma=0.92,"
            "colorbalance="
                "rs=-0.12:gs=-0.04:bs=0.14:"
                "rm=0.08:gm=0.00:bm=-0.06:"
                "rh=0.20:gh=0.06:bh=-0.18,"
            "curves=master='0/0 0.15/0.06 0.5/0.55 0.85/0.92 1/1'"
        )

    if preset == "teal_orange":
        # AGGRESSIVE blockbuster — deep teal shadows, hot orange skin, crushed blacks
        return (
            "eq=contrast=1.42:saturation=1.60:gamma=0.88,"
            "colorbalance="
                "rs=-0.24:gs=-0.08:bs=0.28:"
                "rm=0.15:gm=0.00:bm=-0.14:"
                "rh=0.26:gh=0.05:bh=-0.22,"
            "curves=master='0/0 0.15/0.05 0.5/0.58 0.85/0.95 1/1'"
        )

    if preset == "filmic_neutral":
        # Kodak-ish — gentle but visible filmic curve, +25% sat
        return (
            "eq=contrast=1.22:saturation=1.30:gamma=0.94,"
            "colorbalance="
                "rs=-0.08:gs=-0.02:bs=0.06:"
                "rm=0.08:gm=0.01:bm=-0.06:"
                "rh=0.14:gh=0.04:bh=-0.12,"
            "curves=master='0/0.02 0.20/0.14 0.5/0.5 0.80/0.86 1/0.98'"
        )

    sys.exit(f"❌ Unknown preset: {preset}")


def _build_vf(preset: str) -> str:
    """Full filter chain: tonemap → grade. Empty grade for baseline."""
    grade = _grade_filter(preset)
    return TONEMAP_CHAIN + ("," + grade if grade else "")


def _encode_args(codec: str, quality: int) -> list[str]:
    if codec == "h264":
        # libx264 handles yuv420p; high quality but compact
        return ["-c:v", "libx264", "-preset", "medium", "-crf", str(quality),
                "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    if codec == "prores":
        return ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"]
    sys.exit(f"❌ Unknown codec: {codec}")


def _run(cmd: list[str], label: str) -> bool:
    t0 = time.time()
    print(f"  ▶ {label}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0
    if proc.returncode != 0:
        tail = (proc.stderr or "")[-600:]
        print(f"    ❌ failed in {elapsed:.1f}s\n{tail}")
        return False
    print(f"    ✓ {elapsed:.1f}s")
    return True


def render_one(src: Path, dst: Path, preset: str, codec: str, quality: int,
               trim_start: float | None = None, trim_dur: float | None = None) -> bool:
    """Render one clip with chosen preset. Optionally trim."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()

    vf = _build_vf(preset)

    cmd = [FFMPEG, "-y", "-loglevel", "error", "-stats"]
    if trim_start is not None:
        cmd += ["-ss", f"{trim_start}"]
    cmd += ["-i", str(src)]
    if trim_dur is not None:
        cmd += ["-t", f"{trim_dur}"]
    cmd += ["-vf", vf]
    cmd += _encode_args(codec, quality)
    # Audio: copy if codec compatible, else AAC
    cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += [str(dst)]

    return _run(cmd, f"{src.name} → {dst.name} [{preset}]")


def cmd_samples(args):
    input_dir = args.input.expanduser().resolve()
    if not input_dir.is_dir():
        sys.exit(f"❌ Input dir not found: {input_dir}")

    sample_clip = input_dir / args.sample_clip
    if not sample_clip.exists():
        sys.exit(f"❌ Sample clip not found: {sample_clip}")

    out_dir = input_dir / "samples_color"
    out_dir.mkdir(exist_ok=True)
    print(f"📂 Sample output: {out_dir}")
    print(f"🎬 Source: {sample_clip.name} (trim {args.sample_start}s → {args.sample_start + args.sample_duration}s)")

    presets = ["baseline", "cinematic_warm", "teal_orange", "filmic_neutral"]
    for preset in presets:
        dst = out_dir / f"sample_{preset}.mp4"
        ok = render_one(
            sample_clip, dst, preset, codec="h264", quality=18,
            trim_start=args.sample_start, trim_dur=args.sample_duration,
        )
        if not ok:
            print(f"  ⚠️  Skipping {preset} due to error")

    print(f"\n✅ Samples ready in {out_dir}")
    print(f"   Compare: open '{out_dir}' and play sample_*.mp4 side by side")


def cmd_batch(args):
    input_dir = args.input.expanduser().resolve()
    if not input_dir.is_dir():
        sys.exit(f"❌ Input dir not found: {input_dir}")

    output_dir = (args.output or (input_dir.parent / f"{input_dir.name}_graded")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    clips = sorted(p for p in input_dir.iterdir()
                   if p.is_file() and p.suffix.lower() in VIDEO_EXTS and not p.name.startswith("."))
    if not clips:
        sys.exit(f"❌ No video clips in {input_dir}")

    print(f"📂 Input:  {input_dir} ({len(clips)} clips)")
    print(f"📂 Output: {output_dir}")
    print(f"🎨 Preset: {args.preset}")
    print(f"🎞️  Codec:  {args.codec} (quality={args.quality})\n")

    failed = []
    for i, src in enumerate(clips, 1):
        dst = output_dir / src.name
        if dst.exists() and not args.force:
            print(f"  [{i}/{len(clips)}] {src.name} — already exists, skip (use --force to redo)")
            continue
        print(f"  [{i}/{len(clips)}] {src.name}")
        if not render_one(src, dst, args.preset, args.codec, args.quality):
            failed.append(src.name)

    print(f"\n✅ Done. {len(clips) - len(failed)}/{len(clips)} succeeded")
    if failed:
        print("   Failed:", ", ".join(failed))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["samples", "batch"], required=True)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", type=Path,
                    help="(batch) Output dir. Default: <input>_graded sibling")
    ap.add_argument("--preset", default="cinematic_warm",
                    choices=["cinematic_warm", "teal_orange", "filmic_neutral", "baseline"])
    ap.add_argument("--codec", default="h264", choices=["h264", "prores"])
    ap.add_argument("--quality", type=int, default=18, help="(h264 only) CRF, lower=better")
    ap.add_argument("--sample-clip", help="(samples) Filename in --input to use")
    ap.add_argument("--sample-start", type=float, default=0.0)
    ap.add_argument("--sample-duration", type=float, default=8.0)
    ap.add_argument("--force", action="store_true", help="(batch) Re-render even if dst exists")
    args = ap.parse_args()

    if args.mode == "samples":
        if not args.sample_clip:
            sys.exit("❌ --sample-clip required for samples mode")
        cmd_samples(args)
    else:
        cmd_batch(args)


if __name__ == "__main__":
    main()
