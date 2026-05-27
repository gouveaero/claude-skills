#!/usr/bin/env python3
"""
preview.py — launches Remotion Studio for the given project + opens browser.

Usage:
    python3 preview.py --remotion-dir <output>/remotion
                       [--port 3001] [--no-open] [--composition Reel]
                       [--with-proxy] [--proxy-output <path/to/proxy.mp4>]

Behavior:
- Picks the first free port starting at --port (tries up to +10).
- Spawns `npx remotion studio` in the background.
- Opens http://localhost:<port>/<composition> on macOS via `open`.
- Prints PID + how to stop.
- If --with-proxy (default True): launches render_proxy.py in background
  before opening the Studio, so the proxy renders in parallel while Studio loads.
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

SKILL_SCRIPTS = Path(__file__).resolve().parent


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


def launch_proxy(remotion_dir: Path, proxy_output: Path, composition: str) -> subprocess.Popen | None:
    """
    Launch render_proxy.py as a non-blocking background subprocess.

    render_proxy.py is expected to be in the same scripts/ directory as preview.py.
    If not found, prints a warning and returns None.
    """
    proxy_script = SKILL_SCRIPTS / "render_proxy.py"
    if not proxy_script.exists():
        print(f"  [proxy] render_proxy.py not found at {proxy_script} — skipping proxy render")
        return None

    cmd = [
        sys.executable, str(proxy_script),
        "--remotion-dir", str(remotion_dir),
        "--output", str(proxy_output),
        "--composition", composition,
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=remotion_dir,
        )
        print(f"  [proxy] render_proxy.py started in background (PID {proc.pid})")
        print(f"  [proxy] output -> {proxy_output}")
        return proc
    except Exception as e:
        print(f"  [proxy] Failed to start render_proxy.py: {e}")
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remotion-dir", required=True, type=Path)
    ap.add_argument("--port", type=int, default=3001)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--composition", default="Reel")
    ap.add_argument("--draft", action="store_true",
                    help="Render at 0.5x scale (540x960 instead of 1080x1920) for faster iteration")
    # New flags
    ap.add_argument("--with-proxy", dest="with_proxy",
                    action=argparse.BooleanOptionalAction, default=True,
                    help="Launch render_proxy.py in background before opening Studio (default: True)")
    ap.add_argument("--proxy-output", type=Path, default=None,
                    help="Path for the proxy MP4 (default: <remotion-dir>/../proxy.mp4)")
    args = ap.parse_args()

    remotion_dir = args.remotion_dir.expanduser().resolve()
    if not (remotion_dir / "package.json").exists():
        sys.exit(f"{remotion_dir}/package.json missing — run setup_project.py first")

    port = find_free_port(args.port)
    if port != args.port:
        print(f"  Port {args.port} busy, using {port}")

    # Resolve proxy output path
    if args.proxy_output:
        proxy_output = args.proxy_output.expanduser().resolve()
    else:
        proxy_output = remotion_dir.parent / "proxy.mp4"

    # Draft mode: Studio renders at 0.5x resolution via URL `?scale=0.5` query param
    scale_query = "?scale=0.5" if args.draft else ""
    url = f"http://localhost:{port}/{args.composition}{scale_query}"
    print(f"Launching Remotion Studio at {url}")
    if args.draft:
        print(f"   Draft mode (540x960 instead of 1080x1920) — faster iteration")
    print(f"   cwd: {remotion_dir}")

    # Launch proxy in background BEFORE Studio, so it renders in parallel
    proxy_proc = None
    if args.with_proxy:
        print(f"  [proxy] Starting proxy render in background...")
        proxy_proc = launch_proxy(remotion_dir, proxy_output, args.composition)

    cmd = ["npx", "remotion", "studio", "--port", str(port)]
    proc = subprocess.Popen(cmd, cwd=remotion_dir)
    print(f"   PID: {proc.pid}  — kill with `kill {proc.pid}` when done")
    if proxy_proc:
        print(f"   Proxy PID: {proxy_proc.pid}  — kill with `kill {proxy_proc.pid}` to abort proxy")

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
        print("\nStopping Studio...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

        # Also stop proxy if still running
        if proxy_proc and proxy_proc.poll() is None:
            print("  [proxy] Stopping proxy render...")
            proxy_proc.terminate()
            try:
                proxy_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy_proc.kill()


if __name__ == "__main__":
    main()
