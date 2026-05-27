#!/usr/bin/env python3
"""
build_remotion.py — generates Root.tsx, Reel.tsx, and components/ from edit_plan.json.

Usage:
    python3 build_remotion.py --plan <output>/edit_plan.json
                              --remotion-dir <output>/remotion
                              [--brand-config <path>/.video-editor.json]
                              [--logo <src> --logo-dest <remotion/public/logo.png>]
                              [--no-install]

Steps:
1. Reads edit_plan.json to compute durationInFrames, fps, width, height
2. Reads .video-editor.json (walks up from --plan if --brand-config missing)
3. Copies templates/components/*.{ts,tsx} into <remotion>/src/components/
4. Renders Root.tsx and Reel.tsx by str-replacing {{PLACEHOLDERS}}
5. Writes <remotion>/src/edit_plan.json (consumed by Reel.tsx via import)
6. Writes <remotion>/src/brand_config.json (subset for runtime)
7. Optionally copies logo to <remotion>/public/<logo>
8. Installs @remotion/transitions if missing in package.json
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "templates"


def find_brand_config(start: Path) -> Path | None:
    cur = start.resolve()
    while cur != cur.parent:
        candidate = cur / ".video-editor.json"
        if candidate.exists():
            return candidate
        cur = cur.parent
    return None


def compute_total_duration_frames(plan: dict) -> int:
    fps = int(plan.get("fps", 30))
    total_seconds = 0.0
    for cut in plan.get("v1_main", []):
        total_seconds += float(cut["source_out"]) - float(cut["source_in"])
    # Subtract crossfade overlaps (each transition shortens total by its duration)
    for t in plan.get("transitions", []):
        if t.get("type", "none") != "none":
            total_seconds -= float(t.get("duration_frames", 6)) / fps
    return max(1, int(round(total_seconds * fps)))


def render_template(tmpl_path: Path, replacements: dict[str, str]) -> str:
    text = tmpl_path.read_text()
    for k, v in replacements.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def ensure_components(remotion_dir: Path) -> None:
    src_components = remotion_dir / "src" / "components"
    src_components.mkdir(parents=True, exist_ok=True)
    src = TEMPLATES / "components"
    for f in src.iterdir():
        if f.suffix in {".ts", ".tsx"}:
            shutil.copy2(f, src_components / f.name)


def install_required_packages(remotion_dir: Path) -> None:
    """Install Remotion add-on packages required by the generated Reel.tsx."""
    pkg_path = remotion_dir / "package.json"
    if not pkg_path.exists():
        print(f"  ⚠  No package.json in {remotion_dir} — run setup_project.py first")
        return
    pkg = json.loads(pkg_path.read_text())
    deps = pkg.get("dependencies", {})
    required = ["@remotion/transitions", "@remotion/google-fonts"]
    needed = [p for p in required if p not in deps]
    if not needed:
        print(f"  ✓ All required packages already installed ({', '.join(required)})")
        return
    print(f"  📦 Installing {', '.join(needed)} ...")
    cmd = ["npm", "install", "--save", *needed]
    result = subprocess.run(cmd, cwd=remotion_dir)
    if result.returncode != 0:
        sys.exit(f"❌ npm install failed (exit {result.returncode})")


def install_transitions_if_missing(remotion_dir: Path) -> None:
    """Backwards-compat alias."""
    install_required_packages(remotion_dir)


def derive_brand_subset(brand_config: dict) -> dict:
    """Pick only the fields Reel.tsx reads at runtime."""
    return {
        "brand": {
            "accent_color": brand_config.get("brand", {}).get("accent_color"),
            "text_color": brand_config.get("brand", {}).get("text_color"),
            "primary_color": brand_config.get("brand", {}).get("primary_color"),
            "background_color": brand_config.get("brand", {}).get("background_color"),
            "font_family": brand_config.get("brand", {}).get("font_family", "Inter"),
            "logo": brand_config.get("brand", {}).get("logo"),
        },
        "remotion": brand_config.get("remotion", {}),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--remotion-dir", required=True, type=Path,
                    help="Path to <output>/remotion/ (already scaffolded)")
    ap.add_argument("--brand-config", type=Path)
    ap.add_argument("--logo", type=Path, help="Source logo path (will be copied to public/)")
    ap.add_argument("--no-install", action="store_true",
                    help="Skip npm install of @remotion/transitions")
    args = ap.parse_args()

    plan_path = args.plan.expanduser().resolve()
    if not plan_path.exists():
        sys.exit(f"❌ Plan not found: {plan_path}")
    remotion_dir = args.remotion_dir.expanduser().resolve()
    if not remotion_dir.exists():
        sys.exit(f"❌ Remotion dir not found: {remotion_dir}. Run setup_project.py first.")
    if not (remotion_dir / "package.json").exists():
        sys.exit(f"❌ {remotion_dir}/package.json missing — incomplete scaffold")

    plan = json.loads(plan_path.read_text())

    brand_path = args.brand_config or find_brand_config(plan_path.parent)
    if not brand_path:
        sys.exit(f"❌ No .video-editor.json found near {plan_path}")
    brand_config = json.loads(Path(brand_path).read_text())

    print(f"📋 Plan: {plan_path}")
    print(f"📋 Brand: {brand_path}")
    print(f"📂 Remotion dir: {remotion_dir}")

    # Resolution
    fps = int(plan.get("fps", 30))
    res = plan.get("resolution") or [1080, 1920]
    if isinstance(res, str):
        w, h = (int(x) for x in res.lower().replace(" ", "").split("x"))
    else:
        w, h = int(res[0]), int(res[1])
    duration_frames = compute_total_duration_frames(plan)
    print(f"  ⚙  fps={fps} resolution={w}x{h} duration={duration_frames}f ({duration_frames/fps:.1f}s)")

    # 1. Components
    ensure_components(remotion_dir)
    print(f"  ✓ Copied components → src/components/")

    # 2. Root.tsx
    src_dir = remotion_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    root_tsx = render_template(
        TEMPLATES / "Root.tsx.tmpl",
        {"DURATION_IN_FRAMES": duration_frames, "FPS": fps, "WIDTH": w, "HEIGHT": h},
    )
    (src_dir / "Root.tsx").write_text(root_tsx)
    print(f"  ✓ Wrote src/Root.tsx")

    # 3. Reel.tsx
    reel_tsx = render_template(
        TEMPLATES / "Reel.tsx.tmpl",
        {"DURATION_IN_FRAMES": duration_frames, "FPS": fps, "WIDTH": w, "HEIGHT": h},
    )
    (src_dir / "Reel.tsx").write_text(reel_tsx)
    print(f"  ✓ Wrote src/Reel.tsx")

    # 4. edit_plan.json + brand_config.json (consumed via import in Root.tsx)
    (src_dir / "edit_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2))
    (src_dir / "brand_config.json").write_text(
        json.dumps(derive_brand_subset(brand_config), ensure_ascii=False, indent=2)
    )
    print(f"  ✓ Wrote src/edit_plan.json + src/brand_config.json")

    # 5. Make sure Remotion's index entry points to Root.tsx
    # create-video --blank produces src/index.ts that imports ./Root or ./Composition.
    # We replace any existing index.ts to point to Root.tsx for consistency.
    index_ts = src_dir / "index.ts"
    index_ts.write_text(
        'import { registerRoot } from "remotion";\n'
        'import { RemotionRoot } from "./Root";\n'
        "\n"
        "registerRoot(RemotionRoot);\n"
    )
    print(f"  ✓ Wrote src/index.ts → registerRoot(RemotionRoot)")

    # 6. Logo copy
    logo_src = args.logo
    if not logo_src:
        # Try resolving brand.logo relative to brand config dir
        rel = brand_config.get("brand", {}).get("logo")
        if rel:
            candidate = (Path(brand_path).parent / rel).resolve()
            if candidate.exists():
                logo_src = candidate
    if logo_src and Path(logo_src).exists():
        rel = brand_config.get("brand", {}).get("logo") or Path(logo_src).name
        dst = remotion_dir / "public" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(logo_src, dst)
        print(f"  ✓ Copied logo → public/{rel}")
    else:
        # Strip brand.logo from runtime config so LogoBug short-circuits to null
        # (avoids 404 in Studio + render warnings)
        brand_subset = json.loads((src_dir / "brand_config.json").read_text())
        if brand_subset.get("brand", {}).get("logo"):
            brand_subset["brand"]["logo"] = None
            (src_dir / "brand_config.json").write_text(
                json.dumps(brand_subset, ensure_ascii=False, indent=2)
            )
        print("  ⚠  No logo file found — LogoBug disabled at runtime")

    # 7. Install transitions if missing
    if not args.no_install:
        install_transitions_if_missing(remotion_dir)

    print(f"\n✅ Build complete. Next: `preview.py --remotion-dir {remotion_dir}`")


if __name__ == "__main__":
    main()
