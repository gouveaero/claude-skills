#!/usr/bin/env python3
"""
batch_data_driven.py — render N reels from a CSV/JSON of props.

Each row in the input file becomes one render with that row's fields passed as
`--props` to the composition. Combined with `calculateMetadata` in Root.tsx,
each render gets its own duration, title, brand color, etc.

Use cases:
  - 50 Vhoe reels from aeronaves.csv (one per aircraft)
  - 20 TriboTax reels from precedentes.csv (one per legal precedent)
  - 100 Telesapiens reels from cursos.csv (one per course)

Usage:
    python3 batch_data_driven.py \\
        --data ~/Videos/vhoe/aeronaves.csv \\
        --remotion-dir ~/Videos/vhoe/output/remotion \\
        --composition Reel \\
        --out-dir ~/Videos/vhoe/output/batch/ \\
        [--concurrency 2] \\
        [--filename-template "{slug}-reel.mp4"] \\
        [--props-extra '{"brand":"vhoe"}']

CSV must have a header. JSON must be a list of objects.
The composition's Zod schema validates each row — wrong types fail fast with helpful errors.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def _slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "row"


def load_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with path.open() as f:
            return list(csv.DictReader(f))
    if path.suffix.lower() in {".json", ".jsonl"}:
        if path.suffix.lower() == ".jsonl":
            with path.open() as f:
                return [json.loads(line) for line in f if line.strip()]
        with path.open() as f:
            data = json.load(f)
        if not isinstance(data, list):
            sys.exit("JSON must be a list of objects")
        return data
    sys.exit(f"Unsupported file type: {path.suffix}")


def coerce_types(row: dict) -> dict:
    """CSV gives all strings; try to coerce numerics/bools to satisfy Zod schemas."""
    out: dict = {}
    for k, v in row.items():
        if isinstance(v, str):
            sv = v.strip()
            if sv.lower() in {"true", "false"}:
                out[k] = sv.lower() == "true"
                continue
            try:
                out[k] = int(sv)
                continue
            except ValueError:
                pass
            try:
                out[k] = float(sv)
                continue
            except ValueError:
                pass
            out[k] = sv
        else:
            out[k] = v
    return out


def render_one(
    row: dict,
    idx: int,
    remotion_dir: Path,
    composition: str,
    out_dir: Path,
    filename_template: str,
    props_extra: dict,
) -> tuple[int, dict, Path, int]:
    merged = {**row, **props_extra}
    slug_source = merged.get("slug") or merged.get("title") or merged.get("name") or f"row-{idx:03d}"
    slug = _slugify(str(slug_source))
    filename = filename_template.format(slug=slug, idx=idx, **merged)
    out_path = out_dir / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "npx", "remotion", "render",
        composition,
        str(out_path),
        f"--props={json.dumps(merged)}",
    ]
    print(f"  [{idx:03d}] {filename}  ({len(json.dumps(merged))} chars props)")
    proc = subprocess.run(cmd, cwd=remotion_dir, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"    FAIL: {proc.stderr.strip().splitlines()[-1] if proc.stderr else 'unknown'}")
    return idx, merged, out_path, proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, type=Path, help="CSV or JSON file with one row per reel")
    ap.add_argument("--remotion-dir", required=True, type=Path,
                    help="Remotion project dir (must contain package.json + src/)")
    ap.add_argument("--composition", default="Reel", help="Composition id (default: Reel)")
    ap.add_argument("--out-dir", required=True, type=Path, help="Where to write the N MP4s")
    ap.add_argument("--concurrency", type=int, default=2,
                    help="Parallel renders (default: 2). Watch RAM — each Remotion render eats ~2GB.")
    ap.add_argument("--filename-template", default="{slug}.mp4",
                    help="Output filename. Available placeholders: {slug}, {idx}, plus any row field. Default: {slug}.mp4")
    ap.add_argument("--props-extra", default="{}",
                    help="JSON object merged into every row's props (e.g. shared brand color)")
    ap.add_argument("--limit", type=int, default=None, help="Only process the first N rows (for testing)")
    args = ap.parse_args()

    data_path = args.data.expanduser().resolve()
    remotion_dir = args.remotion_dir.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()

    if not (remotion_dir / "package.json").exists():
        sys.exit(f"Not a Remotion project: {remotion_dir} (missing package.json)")

    rows_raw = load_rows(data_path)
    rows = [coerce_types(r) for r in rows_raw]
    if args.limit:
        rows = rows[: args.limit]

    try:
        props_extra = json.loads(args.props_extra)
    except json.JSONDecodeError as err:
        sys.exit(f"--props-extra is not valid JSON: {err}")

    print(f"Rendering {len(rows)} reels from {data_path.name} -> {out_dir}")
    print(f"  composition={args.composition} concurrency={args.concurrency}")

    failures: list[tuple[int, str]] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = [
            ex.submit(
                render_one,
                row, idx, remotion_dir, args.composition, out_dir,
                args.filename_template, props_extra,
            )
            for idx, row in enumerate(rows)
        ]
        for fut in as_completed(futures):
            idx, merged, out_path, rc = fut.result()
            if rc != 0:
                failures.append((idx, str(out_path)))

    print(f"\nDone: {len(rows) - len(failures)}/{len(rows)} succeeded")
    if failures:
        print("Failed indices:", ", ".join(str(i) for i, _ in failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
