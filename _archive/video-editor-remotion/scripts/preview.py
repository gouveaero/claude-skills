#!/usr/bin/env python3
"""
preview.py — launches Remotion Studio for the given project + opens browser.

Usage:
    python3 preview.py --remotion-dir <output>/remotion
                       [--port 3001] [--no-open] [--composition Reel]

Behavior:
- Picks the first free port starting at --port (tries up to +10).
- Spawns `npx remotion studio` in the background.
- Opens http://localhost:<port>/<composition> on macOS via `open`.
- Prints PID + how to stop.
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


def find_free_port(start: int, attempts: int = 10) -> int:
    for offset in range(attempts):
        port = start + offset
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port in [{start}, {start + attempts})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remotion-dir", required=True, type=Path)
    ap.add_argument("--port", type=int, default=3001)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--composition", default="Reel")
    ap.add_argument("--draft", action="store_true",
                    help="Render at 0.5× scale (540x960 instead of 1080x1920) for faster iteration")
    args = ap.parse_args()

    remotion_dir = args.remotion_dir.expanduser().resolve()
    if not (remotion_dir / "package.json").exists():
        sys.exit(f"❌ {remotion_dir}/package.json missing — run setup_project.py first")

    port = find_free_port(args.port)
    if port != args.port:
        print(f"⚠  Port {args.port} busy, using {port}")

    # Draft mode: Studio renders at 0.5× resolution via URL `?scale=0.5` query param
    # (Studio doesn't accept a CLI flag for this; the scale prop applies during preview).
    scale_query = "?scale=0.5" if args.draft else ""
    url = f"http://localhost:{port}/{args.composition}{scale_query}"
    print(f"🎬 Launching Remotion Studio at {url}")
    if args.draft:
        print(f"   ⚡ Draft mode (540×960 instead of 1080×1920) — faster iteration")
    print(f"   cwd: {remotion_dir}")

    cmd = ["npx", "remotion", "studio", "--port", str(port)]
    proc = subprocess.Popen(cmd, cwd=remotion_dir)
    print(f"   PID: {proc.pid}  — kill with `kill {proc.pid}` when done")

    if not args.no_open:
        # Give Studio ~3s to bind so the browser doesn't hit a connection refused
        time.sleep(3)
        if sys.platform == "darwin":
            subprocess.run(["open", url], check=False)
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", url], check=False)
        else:
            print(f"   Open manually: {url}")

    print("\n   Studio runs in the foreground process — Ctrl+C to stop.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n👋 Stopping Studio...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
