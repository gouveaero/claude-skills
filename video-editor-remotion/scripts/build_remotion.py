#!/usr/bin/env python3
"""
build_remotion.py — generates Root.tsx, Reel.tsx, and components/ from edit_plan.json.

Usage:
    python3 build_remotion.py --plan <output>/edit_plan.json
                              --remotion-dir <output>/remotion
                              [--brand-config <path>/.video-editor.json]
                              [--logo <src> --logo-dest <remotion/public/logo.png>]
                              [--no-install]
                              [--skill-dir <path>]  # override skill root for templates

Steps:
1. Reads edit_plan.json to compute durationInFrames, fps, width, height
2. Reads .video-editor.json (walks up from --plan if --brand-config missing)
3. Copies templates/components/*.{ts,tsx} into <remotion>/src/components/
4. Renders Root.tsx and Reel.tsx by str-replacing {{PLACEHOLDERS}}
5. Writes <remotion>/src/edit_plan.json (consumed by Reel.tsx via import)
6. Writes <remotion>/src/brand_config.json (subset for runtime)
7. Optionally copies logo to <remotion>/public/<logo>
8. Installs @remotion/transitions if missing in package.json
9. Generates isolated <Composition> blocks for overlays_v2 entries that have a component
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Default: skill root is two levels above this script (scripts/ -> skill root)
SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "templates"


# Duration caps per SFX category (in ms). Mirrors capcut_draft_builder.SFX_DURATION_CAPS_MS
# from the parent skill, but applied via Sequence durationInFrames in Reel.tsx instead.
SFX_DURATION_CAPS_MS: dict[str, int] = {
    "WOOSH": 800,
    "CLICK": 400,
    "DIGITAL": 1500,
    "TRANSIÇÃO": 1200,
    "CAMERA": 600,
    "PLIM": 700,
    "RISER": 3500,
    "VARIAVEIS": 2500,
    "AMBIENTE": 6000,
    "CINEMATICA": 4000,
    "ROLAGEM": 2000,
    "GLITCH": 600,
    "TECLADO": 1500,
    "DINHEIRO": 1200,
    "ESTALO": 400,
    "CONTAGEM": 2500,
    "POPS": 500,
    "BOOM": 2000,
    "NOTIFICATION": 800,
    "DRUM": 600,
    "GLASS_BREAK": 1200,
    "APPLAUSE": 3000,
    "HORROR": 3000,
    "FAIL": 2500,
    "MAGIC": 1500,
    "HEARTBEAT": 1500,
}


def resolve_and_copy_sfx(plan: dict, remotion_dir: Path, sfx_index_path: Path | None,
                          reel_name: str) -> dict:
    """For each entry in plan.sfx[], resolve category → concrete file path using
    sfx_index.json + deterministic seed, copy the file to <remotion>/public/sfx/,
    and inject `file` + `duration_cap_ms` fields into the sfx entry.

    Returns the mutated plan (plan.sfx[].file is now populated).
    """
    import random as _random
    sfx_decls = plan.get("sfx") or []
    if not sfx_decls:
        return plan
    if not sfx_index_path or not Path(sfx_index_path).exists():
        print(f"  [WARN] sfx_index.json not found at {sfx_index_path} — SFX will not play in render")
        return plan

    sfx_index = json.loads(Path(sfx_index_path).read_text())
    public_sfx = remotion_dir / "public" / "sfx"
    public_sfx.mkdir(parents=True, exist_ok=True)

    resolved_count = 0
    missing_categories: set[str] = set()

    for i, sfx in enumerate(sfx_decls):
        if not isinstance(sfx, dict):
            continue
        if sfx.get("file"):
            # Already resolved (e.g. from a prior build); skip but ensure file is in public/sfx/
            continue
        category = sfx.get("category")
        if not category:
            continue

        candidates = sfx_index.get(category)
        if not candidates:
            missing_categories.add(category)
            continue

        # Deterministic per (reel_name, category, index) — same plan re-renders identically
        seed = f"{reel_name}-{category}-{i}"
        rng = _random.Random(seed)
        chosen = rng.choice(candidates)
        # `chosen` can be an absolute path string OR a dict with {file: "...", ...}
        if isinstance(chosen, dict):
            chosen_path = chosen.get("path") or chosen.get("file")
        else:
            chosen_path = chosen
        if not chosen_path:
            missing_categories.add(category)
            continue

        src = Path(chosen_path).expanduser()
        if not src.exists():
            print(f"  [WARN] SFX file missing: {src}")
            continue

        dst = public_sfx / src.name
        if not dst.exists():
            shutil.copy2(src, dst)

        sfx["file"] = src.name
        sfx["duration_cap_ms"] = SFX_DURATION_CAPS_MS.get(category)
        resolved_count += 1

    if resolved_count:
        print(f"  Resolved + copied {resolved_count} SFX file(s) -> public/sfx/")
    if missing_categories:
        print(f"  [WARN] No files for categories: {sorted(missing_categories)}")

    return plan


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


def ensure_components(remotion_dir: Path, templates_dir: Path) -> None:
    src_components = remotion_dir / "src" / "components"
    src_components.mkdir(parents=True, exist_ok=True)
    src = templates_dir / "components"
    if not src.exists():
        print(f"  [WARN] components template dir not found: {src}")
        return
    for f in src.iterdir():
        if f.suffix in {".ts", ".tsx"}:
            shutil.copy2(f, src_components / f.name)


# Optional packages — installed only when the plan references the corresponding overlay kind.
# Keeps node_modules slim for simple projects.
OPTIONAL_PACKAGE_TRIGGERS: dict[str, list[str]] = {
    # overlay kind → packages required
    "audio_waveform": ["@remotion/media-utils"],
    "lottie": ["@remotion/lottie"],
    "rive": ["@remotion/rive"],
    "three_reveal": ["@remotion/three", "@react-three/fiber", "@react-three/drei", "three", "@types/three"],
    "motion_blur": ["@remotion/motion-blur"],
    "noise_background": ["@remotion/noise"],
    "shape_morph": ["@remotion/shapes", "@remotion/paths"],
}

# Core packages — always installed (Zod, fonts, transitions, etc.).
CORE_REQUIRED_PACKAGES = [
    "@remotion/transitions",
    "@remotion/google-fonts",
    "@remotion/zod-types",
    "zod",
]


def detect_optional_packages(plan: dict) -> list[str]:
    """Scan plan for overlay kinds that trigger optional packages."""
    kinds = set()
    for ov in plan.get("rich_overlays", []) or []:
        if isinstance(ov, dict) and "kind" in ov:
            kinds.add(ov["kind"])
    for ov in plan.get("overlays_v2", []) or []:
        if isinstance(ov, dict):
            k = ov.get("kind") or ov.get("component")
            if k:
                kinds.add(k)
    packages: list[str] = []
    for kind, pkgs in OPTIONAL_PACKAGE_TRIGGERS.items():
        if kind in kinds:
            packages.extend(pkgs)
    return packages


def install_required_packages(remotion_dir: Path, plan: dict, with_tailwind: bool = False) -> None:
    """Install Remotion add-on packages required by the generated Reel.tsx + plan-specific kinds."""
    pkg_path = remotion_dir / "package.json"
    if not pkg_path.exists():
        print(f"  No package.json in {remotion_dir} — run setup_project.py first")
        return
    pkg = json.loads(pkg_path.read_text())
    deps = pkg.get("dependencies", {})

    required = list(CORE_REQUIRED_PACKAGES)
    required.extend(detect_optional_packages(plan))
    if with_tailwind:
        required.extend(["@remotion/tailwind-v4", "tailwindcss"])

    needed = [p for p in required if p not in deps]
    if not needed:
        print(f"  All required packages already installed")
        return
    print(f"  Installing {', '.join(needed)} ...")
    cmd = ["npm", "install", "--save", *needed]
    result = subprocess.run(cmd, cwd=remotion_dir)
    if result.returncode != 0:
        sys.exit(f"npm install failed (exit {result.returncode})")


def setup_tailwind(remotion_dir: Path) -> None:
    """Drop a minimal Tailwind v4 config + remotion.config.ts override."""
    src_dir = remotion_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "tailwind.css").write_text("@import \"tailwindcss\";\n")
    config_path = remotion_dir / "remotion.config.ts"
    config_snippet = (
        "import { Config } from '@remotion/cli/config';\n"
        "import { enableTailwind } from '@remotion/tailwind-v4';\n\n"
        "Config.overrideWebpackConfig(enableTailwind);\n"
    )
    if config_path.exists():
        existing = config_path.read_text()
        if "enableTailwind" not in existing:
            config_path.write_text(existing + "\n" + config_snippet)
    else:
        config_path.write_text(config_snippet)
    print(f"  Tailwind v4 wired into remotion.config.ts + src/tailwind.css")


def install_transitions_if_missing(remotion_dir: Path, plan: dict | None = None) -> None:
    """Backwards-compat alias. Accepts an optional plan for plan-specific packages."""
    install_required_packages(remotion_dir, plan or {})


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


def _slugify(text: str) -> str:
    """Convert a string to a safe kebab-case slug for use in Composition ids."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return slug or "overlay"


def _pascal_case(text: str) -> str:
    """Convert snake/kebab string to PascalCase for React component names."""
    return "".join(word.capitalize() for word in re.split(r"[_\-\s]+", text) if word)


def build_isolated_overlay_compositions(
    plan: dict,
    src_dir: Path,
    templates_dir: Path,
    fps: int,
    w: int,
    h: int,
) -> list[str]:
    """
    For each entry in plan["overlays_v2"] that has a "component" field,
    generate an isolated <Composition> block.

    Uses templates/overlay_isolated.tsx.tmpl if it exists; otherwise generates inline.

    Returns a list of TSX Composition strings to be appended to Root.tsx.
    """
    overlays_v2 = plan.get("overlays_v2", [])
    compositions: list[str] = []
    tmpl_path = templates_dir / "overlay_isolated.tsx.tmpl"
    has_tmpl = tmpl_path.exists()

    for i, ov in enumerate(overlays_v2):
        component_name = ov.get("component")
        if not component_name:
            continue  # skip overlays that have no explicit React component

        text = ov.get("text", f"overlay_{i}")
        subtext = ov.get("subtext", "")
        start_s = float(ov.get("start", 0.0))
        end_s = float(ov.get("end", start_s + 3.0))
        duration_s = max(0.1, end_s - start_s)
        duration_frames = max(1, round(duration_s * fps))
        slug = _slugify(text)
        composition_id = f"overlay_{i}_{slug}"
        component_path = ov.get("component_path", component_name)

        # Build defaultProps JSON
        default_props = {
            "text": text,
            "startFrame": 0,
            "endFrame": duration_frames,
        }
        if subtext:
            default_props["subtext"] = subtext
        # Merge any extra props from the plan entry
        extra_props = ov.get("props", {})
        default_props.update(extra_props)
        props_json = json.dumps(default_props)

        if has_tmpl:
            tsx = render_template(tmpl_path, {
                "COMPONENT_NAME": component_name,
                "COMPONENT_PATH": component_path,
                "COMPOSITION_ID": composition_id,
                "COMPOSITION_ID_CAMEL": _pascal_case(composition_id),
                "PROPS_JSON": props_json,
                "WIDTH": w,
                "HEIGHT": h,
                "FPS": fps,
                "DURATION_S": f"{duration_s:.3f}",
            })
        else:
            # Inline fallback — generates a self-contained Composition block
            tsx = f"""\
// Isolated overlay composition — generated by build_remotion.py
// Component: {component_name} | id: {composition_id}
<Composition
  id="{composition_id}"
  component={{{component_name}}}
  durationInFrames={{{duration_frames}}}
  fps={{{fps}}}
  width={{{w}}}
  height={{{h}}}
  defaultProps={{{props_json}}}
/>"""

        compositions.append(tsx)
        print(f"  Overlay composition: {composition_id} ({duration_frames}f @ {fps}fps)")

    return compositions


def inject_overlay_compositions_into_root(root_tsx: str, overlay_compositions: list[str]) -> str:
    """
    Inject isolated overlay <Composition> blocks into Root.tsx.

    Strategy: find the closing </> or </RemotionRoot> tag and insert before it.
    Falls back to appending a comment block at the end if no closing tag is found.
    """
    if not overlay_compositions:
        return root_tsx

    overlay_block = "\n\n      {/* === Isolated overlay compositions (generated) === */}\n"
    for comp in overlay_compositions:
        # Indent each line by 6 spaces to match typical Root.tsx formatting
        indented = "\n".join("      " + line if line.strip() else line
                             for line in comp.splitlines())
        overlay_block += f"\n{indented}\n"

    # Try to insert before closing fragment tag
    for closing_tag in ["</>", "</RemotionRoot>", "</React.Fragment>"]:
        if closing_tag in root_tsx:
            return root_tsx.replace(closing_tag, overlay_block + closing_tag, 1)

    # Last resort: append with a clear marker
    return root_tsx + "\n\n// === OVERLAY COMPOSITIONS ===\n" + overlay_block


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--remotion-dir", required=True, type=Path,
                    help="Path to <output>/remotion/ (already scaffolded)")
    ap.add_argument("--brand-config", type=Path)
    ap.add_argument("--logo", type=Path, help="Source logo path (will be copied to public/)")
    ap.add_argument("--sfx-index", type=Path, default=None,
                    help="Override sfx_index.json path (default: <skill>/assets/sfx_index.json)")
    ap.add_argument("--no-install", action="store_true",
                    help="Skip npm install of @remotion/* add-on packages")
    ap.add_argument("--with-tailwind", action="store_true",
                    help="Enable @remotion/tailwind-v4 (writes remotion.config.ts + src/tailwind.css)")
    ap.add_argument("--skill-dir", type=Path, default=None,
                    help="Override skill root directory for locating templates/")
    args = ap.parse_args()

    # Allow --skill-dir to override the auto-detected SKILL_ROOT
    skill_root = args.skill_dir.expanduser().resolve() if args.skill_dir else SKILL_ROOT
    templates_dir = skill_root / "templates"

    plan_path = args.plan.expanduser().resolve()
    if not plan_path.exists():
        sys.exit(f"Plan not found: {plan_path}")
    remotion_dir = args.remotion_dir.expanduser().resolve()
    if not remotion_dir.exists():
        sys.exit(f"Remotion dir not found: {remotion_dir}. Run setup_project.py first.")
    if not (remotion_dir / "package.json").exists():
        sys.exit(f"{remotion_dir}/package.json missing — incomplete scaffold")

    plan = json.loads(plan_path.read_text())

    brand_path = args.brand_config or find_brand_config(plan_path.parent)
    if not brand_path:
        sys.exit(f"No .video-editor.json found near {plan_path}")
    brand_config = json.loads(Path(brand_path).read_text())

    print(f"Plan: {plan_path}")
    print(f"Brand: {brand_path}")
    print(f"Remotion dir: {remotion_dir}")
    print(f"Templates dir: {templates_dir}")

    # Resolution
    fps = int(plan.get("fps", 30))
    res = plan.get("resolution") or [1080, 1920]
    if isinstance(res, str):
        w, h = (int(x) for x in res.lower().replace(" ", "").split("x"))
    else:
        w, h = int(res[0]), int(res[1])
    duration_frames = compute_total_duration_frames(plan)
    print(f"  fps={fps} resolution={w}x{h} duration={duration_frames}f ({duration_frames/fps:.1f}s)")

    # 1. Components
    ensure_components(remotion_dir, templates_dir)
    print(f"  Copied components -> src/components/")

    # 2. Root.tsx
    src_dir = remotion_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    root_tmpl = templates_dir / "Root.tsx.tmpl"
    if root_tmpl.exists():
        duration_ms_default = int(round((duration_frames / fps) * 1000))
        root_tsx = render_template(
            root_tmpl,
            {
                "DURATION_IN_FRAMES": duration_frames,
                "DURATION_MS_DEFAULT": duration_ms_default,
                "FPS": fps,
                "WIDTH": w,
                "HEIGHT": h,
            },
        )
    else:
        # Minimal fallback Root.tsx if template is missing
        root_tsx = (
            'import { Composition } from "remotion";\n'
            'import { Reel } from "./Reel";\n\n'
            "export const RemotionRoot: React.FC = () => {\n"
            "  return (\n"
            "    <>\n"
            f'      <Composition id="Reel" component={{Reel}} durationInFrames={{{duration_frames}}}'
            f' fps={{{fps}}} width={{{w}}} height={{{h}}} />\n'
            "    </>\n"
            "  );\n"
            "};\n"
        )

    # Generate and inject isolated overlay compositions
    overlay_compositions = build_isolated_overlay_compositions(
        plan, src_dir, templates_dir, fps, w, h
    )
    if overlay_compositions:
        root_tsx = inject_overlay_compositions_into_root(root_tsx, overlay_compositions)
        print(f"  Injected {len(overlay_compositions)} isolated overlay composition(s) into Root.tsx")

    (src_dir / "Root.tsx").write_text(root_tsx)
    print(f"  Wrote src/Root.tsx")

    # 3. Reel.tsx
    reel_tmpl = templates_dir / "Reel.tsx.tmpl"
    if reel_tmpl.exists():
        reel_tsx = render_template(
            reel_tmpl,
            {"DURATION_IN_FRAMES": duration_frames, "FPS": fps, "WIDTH": w, "HEIGHT": h},
        )
        (src_dir / "Reel.tsx").write_text(reel_tsx)
        print(f"  Wrote src/Reel.tsx")
    else:
        print(f"  [WARN] Reel.tsx.tmpl not found in {templates_dir} — skipping Reel.tsx")

    # 3b. ReelThumbnail.tsx (used by the <Still id="reel-thumbnail"> composition)
    thumb_tmpl = templates_dir / "ReelThumbnail.tsx.tmpl"
    if thumb_tmpl.exists():
        thumb_tsx = render_template(
            thumb_tmpl,
            {"FPS": fps, "WIDTH": w, "HEIGHT": h},
        )
        (src_dir / "ReelThumbnail.tsx").write_text(thumb_tsx)
        print(f"  Wrote src/ReelThumbnail.tsx")

    # 3c. Resolve SFX categories → concrete files + copy to public/sfx/.
    # Mutates plan.sfx[] in place — `file` and `duration_cap_ms` are populated.
    sfx_index_default = SKILL_ROOT / "assets" / "sfx_index.json"
    sfx_index_path = args.sfx_index if args.sfx_index else sfx_index_default
    reel_name = plan.get("reel_name") or plan_path.stem or "reel"
    plan = resolve_and_copy_sfx(plan, remotion_dir, sfx_index_path, reel_name)

    # Also persist the resolved plan to the output dir (alongside the canonical edit_plan.json)
    resolved_plan_path = plan_path.parent / "edit_plan_resolved.json"
    resolved_plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))
    print(f"  Wrote {resolved_plan_path.name}")

    # 4. edit_plan.json + brand_config.json (consumed via import in Root.tsx)
    (src_dir / "edit_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2))
    (src_dir / "brand_config.json").write_text(
        json.dumps(derive_brand_subset(brand_config), ensure_ascii=False, indent=2)
    )
    print(f"  Wrote src/edit_plan.json + src/brand_config.json")

    # 5. Make sure Remotion's index entry points to Root.tsx
    index_ts = src_dir / "index.ts"
    index_ts.write_text(
        'import { registerRoot } from "remotion";\n'
        'import { RemotionRoot } from "./Root";\n'
        "\n"
        "registerRoot(RemotionRoot);\n"
    )
    print(f"  Wrote src/index.ts -> registerRoot(RemotionRoot)")

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
        print(f"  Copied logo -> public/{rel}")
    else:
        # Strip brand.logo from runtime config so LogoBug short-circuits to null
        brand_subset = json.loads((src_dir / "brand_config.json").read_text())
        if brand_subset.get("brand", {}).get("logo"):
            brand_subset["brand"]["logo"] = None
            (src_dir / "brand_config.json").write_text(
                json.dumps(brand_subset, ensure_ascii=False, indent=2)
            )
        print("  No logo file found — LogoBug disabled at runtime")

    # 7. Install required + plan-specific packages
    if not args.no_install:
        install_required_packages(remotion_dir, plan, with_tailwind=args.with_tailwind)
    if args.with_tailwind:
        setup_tailwind(remotion_dir)

    print(f"\nBuild complete. Next: `preview.py --remotion-dir {remotion_dir}`")


if __name__ == "__main__":
    main()
