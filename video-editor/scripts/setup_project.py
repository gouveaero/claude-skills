#!/usr/bin/env python3
"""
setup_project.py — scaffolds a Remotion project + transcodes HEVC/4K clips to H.264 1080p.

Usage:
    python3 setup_project.py --input <clips_dir> [--name <reel-name>]
                             [--proxy-resolution 1080] [--no-scaffold]

Steps:
1. Walk-up from --input to find .video-editor.json (--brand-config to override)
2. Create <ClientFolder>/output/<reel-name>/
3. Detect clips, transcode HEVC/4K → H.264 yuv420p 1920x1080 30fps in clips_proxy/ (cached)
4. `npx create-video@latest --yes --blank` into output/<reel>/remotion/
5. Copy proxies into remotion/public/clips/

Subsequent runs are idempotent: skips transcode and scaffold if already present.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}


def find_brand_config(start: Path) -> tuple[Path | None, Path | None]:
    cur = start.resolve()
    while cur != cur.parent:
        candidate = cur / ".video-editor.json"
        if candidate.exists():
            return candidate, cur
        cur = cur.parent
    return None, None


def probe_clip(path: Path) -> dict:
    """Return {codec, pix_fmt, width, height, fps, duration} via ffprobe."""
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name,pix_fmt,width,height,r_frame_rate",
         "-show_entries", "format=duration",
         "-of", "json", str(path)],
        text=True
    )
    data = json.loads(out)
    s = data.get("streams", [{}])[0]
    fmt = data.get("format", {})
    fps_raw = s.get("r_frame_rate", "30/1")
    try:
        a, b = fps_raw.split("/")
        fps = float(a) / float(b) if float(b) else 30.0
    except Exception:
        fps = 30.0
    return {
        "codec": s.get("codec_name", "unknown"),
        "pix_fmt": s.get("pix_fmt", "unknown"),
        "width": int(s.get("width", 0)),
        "height": int(s.get("height", 0)),
        "fps": fps,
        "duration": float(fmt.get("duration", 0.0)),
    }


def needs_transcode(probe: dict, target_height: int = 1080) -> bool:
    """HEVC / 10-bit / >1080p / weird pix_fmt → transcode."""
    if probe["codec"] in {"hevc", "h265", "vp9", "av1"}:
        return True
    if "10le" in probe["pix_fmt"] or "12le" in probe["pix_fmt"]:
        return True
    if probe["height"] > target_height:
        return True
    if probe["pix_fmt"] not in {"yuv420p", "yuvj420p"}:
        return True
    return False


def transcode_clip(src: Path, dst: Path, target_height: int = 1080) -> bool:
    """Transcode to H.264 yuv420p, scale to target_height keeping aspect."""
    if dst.exists() and dst.stat().st_size > 0 and dst.stat().st_mtime >= src.stat().st_mtime:
        return True
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(src),
        "-vf", f"scale=-2:{target_height}:flags=lanczos",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(dst),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and dst.exists() and dst.stat().st_size > 0


def scaffold_remotion(remotion_dir: Path) -> bool:
    """Run `npx create-video@latest --yes --blank` if package.json doesn't exist."""
    if (remotion_dir / "package.json").exists():
        print(f"  ✓ Remotion project already scaffolded at {remotion_dir}")
        return True
    remotion_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"  📦 Scaffolding Remotion project (this takes ~1 min)...")
    # create-video creates the dir; we run from parent
    cmd = ["npx", "--yes", "create-video@latest", "--yes", "--blank", remotion_dir.name]
    result = subprocess.run(cmd, cwd=remotion_dir.parent, capture_output=False)
    if result.returncode != 0:
        print(f"  ❌ Scaffold failed (exit {result.returncode})")
        return False
    return (remotion_dir / "package.json").exists()


def copy_clips_to_public(clip_paths: list[Path], remotion_dir: Path) -> int:
    """Copy transcoded clips into remotion/public/clips/."""
    public_clips = remotion_dir / "public" / "clips"
    public_clips.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in clip_paths:
        dst = public_clips / src.name
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            continue
        shutil.copy2(src, dst)
        copied += 1
    return copied


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path, help="Directory with raw clips")
    ap.add_argument("--name", help="Reel name (kebab-case). Default: input dir name")
    ap.add_argument("--brand-config", type=Path, help="Override .video-editor.json path")
    ap.add_argument("--proxy-resolution", type=int, default=1080, help="Target height for proxies (default 1080)")
    ap.add_argument("--no-scaffold", action="store_true", help="Skip npx create-video step")
    args = ap.parse_args()

    input_dir = args.input.expanduser().resolve()
    if not input_dir.is_dir():
        sys.exit(f"❌ Input not a dir: {input_dir}")

    if args.brand_config:
        brand_path = args.brand_config.expanduser().resolve()
        client_root = brand_path.parent
    else:
        brand_path, client_root = find_brand_config(input_dir)
        if not brand_path:
            sys.exit(f"❌ No .video-editor.json found walking up from {input_dir}")

    name = args.name or input_dir.name.replace(" ", "_").lower()
    output_dir = client_root / "output" / name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📋 Brand config: {brand_path}")
    print(f"📂 Output dir: {output_dir}")

    # 1. Discover & transcode clips
    clips = sorted(p for p in input_dir.iterdir()
                   if p.is_file() and p.suffix.lower() in VIDEO_EXTS and not p.name.startswith("."))
    if not clips:
        sys.exit(f"❌ No video clips in {input_dir}")
    print(f"🎬 {len(clips)} clip(s) found")

    proxy_dir = output_dir / "clips_proxy"
    proxy_dir.mkdir(exist_ok=True)
    proxy_paths = []
    for clip in clips:
        probe = probe_clip(clip)
        proxy_path = proxy_dir / clip.name
        if needs_transcode(probe, args.proxy_resolution):
            print(f"  ⚙️  {clip.name} ({probe['codec']} {probe['width']}x{probe['height']}) → H.264 {args.proxy_resolution}p")
            if not transcode_clip(clip, proxy_path, args.proxy_resolution):
                print(f"     ❌ Transcode failed for {clip.name}")
                continue
        else:
            # Already friendly — symlink or copy
            if not proxy_path.exists():
                shutil.copy2(clip, proxy_path)
            print(f"  ✓ {clip.name} (no transcode needed)")
        proxy_paths.append(proxy_path)

    print(f"   Proxies ready in {proxy_dir} ({len(proxy_paths)})")

    # 2. Scaffold Remotion project
    remotion_dir = output_dir / "remotion"
    if not args.no_scaffold:
        if not scaffold_remotion(remotion_dir):
            sys.exit("❌ Scaffold failed")

    # 3. Copy proxies → public/clips
    if remotion_dir.exists():
        copied = copy_clips_to_public(proxy_paths, remotion_dir)
        print(f"  ✓ Copied {copied} clip(s) to remotion/public/clips/")

    print(f"\n✅ Setup complete. Next: `transcribe.py --input {input_dir}`")


if __name__ == "__main__":
    main()
