#!/usr/bin/env python3
"""
render_thumbnail.py — render a single frame of the reel as a PNG cover image.

Uses the <Still id="reel-thumbnail"> composition defined in Root.tsx.tmpl.
Pick the frame either by frame index, milliseconds into the reel, or by named
hook from edit_plan.json (e.g. "first_hook", "climax").

Usage:
    python3 render_thumbnail.py \\
        --remotion-dir <output>/remotion \\
        --out <output>/thumbnail.png \\
        [--frame-ms 80000  | --frame 2400  | --hook climax] \\
        [--title "TÍTULO DA CAPA"]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def hook_to_frame_index(plan: dict, hook_name: str, fps: int) -> int:
    """Resolve a named hook in the plan to a frame index."""
    # Convention: plan can declare named timestamps under "thumbnail_anchors":
    #   { "thumbnail_anchors": { "climax": 78000, "first_hook": 1500 } }
    anchors = plan.get("thumbnail_anchors", {}) if isinstance(plan, dict) else {}
    if hook_name in anchors:
        ms = anchors[hook_name]
        return int(round((ms / 1000) * fps))
    # Fallback: search rich_overlays for kind=="cinematic_title" or text matching hook_name
    for ov in plan.get("rich_overlays", []) or []:
        if not isinstance(ov, dict):
            continue
        if ov.get("kind") == "cinematic_title" and hook_name.lower() in (ov.get("text", "").lower()):
            return int(round((ov.get("start", 0)) * fps))
    sys.exit(f"Could not resolve hook '{hook_name}' in plan. Add it to thumbnail_anchors or use --frame-ms.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remotion-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path, help="Output PNG path")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--frame-ms", type=int, help="Frame at this many milliseconds into the reel")
    g.add_argument("--frame", type=int, help="Frame index (integer)")
    g.add_argument("--hook", type=str, help="Named hook from plan.thumbnail_anchors")
    ap.add_argument("--title", default=None, help="Optional title text overlaid on the thumbnail")
    ap.add_argument("--composition", default="reel-thumbnail",
                    help="Composition id (default: reel-thumbnail)")
    args = ap.parse_args()

    remotion_dir = args.remotion_dir.expanduser().resolve()
    out_path = args.out.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plan_path = remotion_dir / "src" / "edit_plan.json"
    plan = json.loads(plan_path.read_text()) if plan_path.exists() else {}
    fps = int(plan.get("fps", 30))

    # Resolve frame index from one of the input modes
    if args.frame is not None:
        frame_idx = args.frame
    elif args.frame_ms is not None:
        frame_idx = int(round((args.frame_ms / 1000) * fps))
    else:
        frame_idx = hook_to_frame_index(plan, args.hook, fps)

    props: dict = {"frameIndex": frame_idx}
    if args.title:
        props["title"] = args.title

    cmd = [
        "npx", "remotion", "still",
        args.composition,
        str(out_path),
        f"--frame={frame_idx}",
        f"--props={json.dumps(props)}",
    ]
    print(f"Rendering frame {frame_idx} ({frame_idx / fps:.2f}s @ {fps}fps) -> {out_path}")
    proc = subprocess.run(cmd, cwd=remotion_dir)
    if proc.returncode != 0:
        sys.exit(proc.returncode)
    print(f"Thumbnail: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
