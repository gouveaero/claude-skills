#!/usr/bin/env python3
"""
render_proxy.py — Fase 7b do pipeline video-editor
Renderiza proxy MP4 540x960 (ou 960x540 pra 16:9) para revisão offline.

Uso:
  python render_proxy.py --remotion-dir <remotion/> --output <proxy.mp4> [--aspect 9:16]
"""
import argparse, subprocess, sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--remotion-dir", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--aspect", default="9:16", choices=["9:16", "16:9"])
    p.add_argument("--concurrency", type=int, default=4)
    args = p.parse_args()

    remotion_dir = Path(args.remotion_dir)
    if not remotion_dir.exists():
        print(f"Erro: pasta remotion não encontrada: {remotion_dir}", file=sys.stderr)
        sys.exit(1)

    scale = 0.5  # 540x960 ou 960x540
    print(f"Renderizando proxy (scale={scale}, crf=28)...")

    cmd = [
        "npx", "remotion", "render", "Reel",
        str(args.output),
        f"--scale={scale}",
        "--codec=h264",
        "--crf=28",
        f"--concurrency={args.concurrency}",
        "--log=error"
    ]

    result = subprocess.run(cmd, cwd=str(remotion_dir))
    if result.returncode != 0:
        print("Erro ao renderizar proxy.", file=sys.stderr)
        sys.exit(1)

    size_mb = Path(args.output).stat().st_size / 1_048_576
    print(f"Proxy gerado: {args.output} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
