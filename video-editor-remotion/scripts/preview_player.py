#!/usr/bin/env python3
"""
preview_player.py — serve an embeddable Remotion <Player> for client approval.

Creates a tiny static HTML page that mounts @remotion/player with the current
reel composition. Useful for sharing a URL with the client (TriboTax, Telesapiens, etc.)
to approve the reel BEFORE the final render — they get controls (play/pause/scrub)
and can see the actual motion-graphics output without needing CapCut.

Two modes:
  1. --bundle (default): pre-bundle the Remotion project with `bundle()` and serve
     the bundle on a local port via `npx serve`.
  2. --studio:           fall back to `npx remotion studio` (full dev experience but
                          dev-friendly only; not for sharing externally).

Usage:
    python3 preview_player.py --remotion-dir <output>/remotion --port 8123
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PLAYER_HTML = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{title}</title>
  <style>
    html, body {{
      margin: 0; padding: 0; height: 100%;
      background: #0A0A0A; color: #F5F1E8;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    .wrap {{
      display: flex; flex-direction: column; align-items: center;
      gap: 12px; padding: 24px;
    }}
    .player {{
      width: min(90vw, {width}px); aspect-ratio: {width}/{height};
      background: #000; border-radius: 8px; overflow: hidden;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }}
    h1 {{ font-size: 18px; margin: 0; letter-spacing: 1px; opacity: 0.8; }}
    .note {{ opacity: 0.5; font-size: 13px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{title}</h1>
    <div class="player">
      <iframe src="./bundle/index.html?composition={composition}"
              style="width:100%; height:100%; border:0;" allowfullscreen></iframe>
    </div>
    <div class="note">Bundle preview · Frame-accurate, interactive · @remotion/player</div>
  </div>
</body>
</html>
"""


def bundle_project(remotion_dir: Path, out_dir: Path) -> None:
    """Use @remotion/bundler to produce a static bundle."""
    bundle_dir = out_dir / "bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    # Run the bundle script (we use the CLI form for simplicity)
    cmd = ["npx", "remotion", "bundle", "src/index.ts", "--out-dir", str(bundle_dir)]
    proc = subprocess.run(cmd, cwd=remotion_dir)
    if proc.returncode != 0:
        # Fallback: older Remotion versions use 'remotion render --bundle-only'
        cmd = ["npx", "remotion", "render", "--bundle-only", str(bundle_dir)]
        proc = subprocess.run(cmd, cwd=remotion_dir)
        if proc.returncode != 0:
            sys.exit("`npx remotion bundle` failed — check Remotion version.")


def write_player_html(out_dir: Path, composition: str, title: str, width: int, height: int) -> None:
    html = PLAYER_HTML.format(
        title=title, composition=composition, width=width, height=height,
    )
    (out_dir / "index.html").write_text(html)


def serve(out_dir: Path, port: int) -> None:
    print(f"\nServing preview on http://localhost:{port}/")
    print("  Share this URL with the client. Stop with Ctrl-C.\n")
    cmd = ["npx", "serve", str(out_dir), "-l", str(port), "--no-clipboard"]
    subprocess.run(cmd)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remotion-dir", required=True, type=Path)
    ap.add_argument("--port", type=int, default=8123)
    ap.add_argument("--composition", default="Reel")
    ap.add_argument("--title", default="Preview — aprovação cliente")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--studio", action="store_true",
                    help="Fallback to `npx remotion studio` (dev only, not for sharing)")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="Where to write the player HTML + bundle (default: <remotion>/preview/)")
    args = ap.parse_args()

    remotion_dir = args.remotion_dir.expanduser().resolve()

    if args.studio:
        cmd = ["npx", "remotion", "studio", "--port", str(args.port)]
        subprocess.run(cmd, cwd=remotion_dir)
        return 0

    out_dir = (args.out_dir or remotion_dir / "preview").expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Bundling Remotion project from {remotion_dir} ...")
    bundle_project(remotion_dir, out_dir)
    write_player_html(out_dir, args.composition, args.title, args.width, args.height)
    print(f"Bundle ready in {out_dir}")

    if shutil.which("npx") is None:
        sys.exit("npx not found — install Node.js to serve the preview")

    serve(out_dir, args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
