#!/usr/bin/env python3
"""
batch_render.py — render multiple variants of a Reel from a CSV.

Usage:
    python3 batch_render.py --remotion-dir <output>/remotion --csv <output>/variants.csv
                            [--composition Reel] [--out-dir <output>/variants]

CSV format (header required):
    name,hook_index,caption_color_override,aspect,codec,scale,extra_props_json

Each row produces one MP4 named <out-dir>/<name>.mp4.
Empty cells fall back to defaults. extra_props_json is merged into --props.
Renders sequentially (Remotion already saturates CPU per render).
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remotion-dir", required=True, type=Path)
    ap.add_argument("--csv", required=True, type=Path)
    ap.add_argument("--composition", default="Reel")
    ap.add_argument("--out-dir", type=Path)
    args = ap.parse_args()

    remotion_dir = args.remotion_dir.expanduser().resolve()
    csv_path = args.csv.expanduser().resolve()
    out_dir = (args.out_dir or remotion_dir.parent / "variants").expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        sys.exit(f"❌ CSV not found: {csv_path}")

    rows = list(csv.DictReader(csv_path.open()))
    if not rows:
        sys.exit(f"❌ CSV has no rows: {csv_path}")

    print(f"📋 {len(rows)} variant(s) → {out_dir}")
    successes = []
    failures = []
    for i, row in enumerate(rows, 1):
        name = (row.get("name") or f"variant_{i:02d}").strip()
        out_path = out_dir / f"{name}.mp4"

        # Build props
        props = {}
        for key in ("hook_index", "caption_color_override", "aspect"):
            val = (row.get(key) or "").strip()
            if val:
                if key == "hook_index":
                    try:
                        props[key] = int(val)
                    except ValueError:
                        props[key] = val
                else:
                    props[key] = val
        extra = (row.get("extra_props_json") or "").strip()
        if extra:
            try:
                props.update(json.loads(extra))
            except json.JSONDecodeError as e:
                print(f"  ⚠ row {i} {name}: bad extra_props_json ({e}) — skipping field")

        cmd = [
            sys.executable, str(SCRIPT_DIR / "render.py"),
            "--remotion-dir", str(remotion_dir),
            "--out", str(out_path),
            "--composition", args.composition,
        ]
        if (row.get("codec") or "").strip():
            cmd += ["--codec", row["codec"].strip()]
        if (row.get("scale") or "").strip():
            cmd += ["--scale", row["scale"].strip()]
        if props:
            cmd += ["--props", json.dumps(props)]

        print(f"\n━━━ [{i}/{len(rows)}] {name} ━━━")
        result = subprocess.run(cmd)
        if result.returncode == 0 and out_path.exists():
            successes.append(out_path)
        else:
            failures.append(name)

    print(f"\n✅ {len(successes)}/{len(rows)} succeeded.")
    if failures:
        print(f"❌ Failed: {', '.join(failures)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
