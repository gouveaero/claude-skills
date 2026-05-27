#!/usr/bin/env python3
"""Audit a site repo for existing tracking tags.

Usage:
    python audit_existing_tags.py /path/to/site

Reports:
    - GTM containers found (GTM-XXXXXXX)
    - Meta Pixel calls (fbq) + Pixel IDs in fbq('init', ...)
    - GA4 / Google Ads tags (gtag / googletagmanager) + IDs (G-..., AW-...)
    - TikTok Pixel (ttq) + Pixel IDs in ttq.load(...)
    - Whether the universal track() layer is already installed
    - Form selectors that look like lead-capture targets

Designed for the `audit` and `gtm-migration` modes of tracking-pixels.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PATTERNS = {
    "gtm_container": re.compile(r"GTM-[A-Z0-9]{6,8}"),
    "meta_pixel_id_init": re.compile(r"""fbq\s*\(\s*['"]init['"]\s*,\s*['"](\d{10,16})['"]"""),
    "ga4_measurement_id": re.compile(r"""G-[A-Z0-9]{8,12}"""),
    "google_ads_conversion_id": re.compile(r"""AW-\d{8,12}"""),
    "tiktok_pixel_id_load": re.compile(r"""ttq\.load\s*\(\s*['"]([A-Z0-9]{15,30})['"]"""),
    "fbq_track_call": re.compile(r"""fbq\s*\(\s*['"]track['"]\s*,\s*['"]([A-Za-z]+)['"]"""),
    "gtag_event_call": re.compile(r"""gtag\s*\(\s*['"]event['"]\s*,\s*['"]([A-Za-z_]+)['"]"""),
    "ttq_track_call": re.compile(r"""ttq\.track\s*\(\s*['"]([A-Za-z]+)['"]"""),
    "universal_track_import": re.compile(r"""from\s+['"][^'"]*lib/track['"]"""),
    "form_id": re.compile(r"""<form[^>]*\bid=['"]([^'"]+)['"]"""),
    "form_data_form": re.compile(r"""<form[^>]*\bdata-form=['"]([^'"]+)['"]"""),
    "gtm_script_tag": re.compile(r"""googletagmanager\.com/gtm\.js\?id="""),
}

EXTENSIONS = {".html", ".htm", ".tsx", ".jsx", ".ts", ".js", ".vue", ".astro"}
SKIP_DIRS = {"node_modules", ".next", "dist", "build", ".git", "coverage", ".turbo"}


def walk_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in EXTENSIONS:
            continue
        yield path


def scan(site: Path) -> dict:
    findings: dict[str, dict] = {k: {} for k in PATTERNS}
    file_count = 0
    for path in walk_files(site):
        file_count += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for key, pat in PATTERNS.items():
            for m in pat.finditer(text):
                captured = m.group(1) if m.lastindex else m.group(0)
                rel = str(path.relative_to(site))
                findings[key].setdefault(captured, []).append(rel)
    return {"files_scanned": file_count, "findings": findings}


def format_report(result: dict, site: Path) -> str:
    f = result["findings"]
    n = result["files_scanned"]
    lines: list[str] = []
    lines.append(f"# Tracking audit — {site}")
    lines.append(f"Scanned {n} files (extensions: html, tsx, jsx, ts, js, vue, astro).\n")

    def section(title: str, key: str, formatter=lambda k: k) -> None:
        if not f[key]:
            return
        lines.append(f"## {title}")
        for value, paths in sorted(f[key].items()):
            lines.append(f"- **{formatter(value)}** — found in {len(paths)} file(s):")
            for p in paths[:5]:
                lines.append(f"  - `{p}`")
            if len(paths) > 5:
                lines.append(f"  - …and {len(paths) - 5} more")
        lines.append("")

    section("GTM containers", "gtm_container")
    section("Meta Pixel IDs (init)", "meta_pixel_id_init")
    section("GA4 Measurement IDs", "ga4_measurement_id")
    section("Google Ads Conversion IDs", "google_ads_conversion_id")
    section("TikTok Pixel IDs", "tiktok_pixel_id_load")
    section("fbq('track', …) event names", "fbq_track_call")
    section("gtag('event', …) event names", "gtag_event_call")
    section("ttq.track(…) event names", "ttq_track_call")

    if f["universal_track_import"]:
        lines.append("## ✅ Universal track() layer already installed")
        for _, paths in f["universal_track_import"].items():
            for p in paths[:10]:
                lines.append(f"- `{p}`")
        lines.append("")
    else:
        lines.append("## ❌ Universal track() layer NOT detected")
        lines.append("Install with `tracking-pixels` skill in `install` mode.\n")

    if f["form_id"] or f["form_data_form"]:
        lines.append("## Forms detected (candidate selectors for Lead/SubmitForm event)")
        for value, paths in sorted(f["form_id"].items()):
            lines.append(f"- `#{value}` — `{paths[0]}`")
        for value, paths in sorted(f["form_data_form"].items()):
            lines.append(f"- `[data-form='{value}']` — `{paths[0]}`")
        lines.append("")

    # Migration verdict
    has_gtm = bool(f["gtm_container"]) or bool(f["gtm_script_tag"])
    has_native = bool(f["universal_track_import"])
    lines.append("## Verdict")
    if has_gtm and not has_native:
        lines.append("**GTM-only setup detected.** Recommended mode: `gtm-migration` (install native in parallel, validate parity, then disable GTM).")
    elif has_gtm and has_native:
        lines.append("**GTM + native coexistence.** Continue parity monitoring; remove GTM once dedup confirmed in Events Manager.")
    elif not has_gtm and has_native:
        lines.append("**Native-only.** Tracking is already installed natively. Use `add-event` or `add-platform` for incremental changes.")
    else:
        lines.append("**No tracking detected.** Recommended mode: `install` (full first-time install).")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path, help="Path to site repo root")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of markdown report")
    args = parser.parse_args()

    if not args.site.exists():
        print(f"error: {args.site} does not exist", file=sys.stderr)
        return 1
    if not args.site.is_dir():
        print(f"error: {args.site} is not a directory", file=sys.stderr)
        return 1

    result = scan(args.site)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_report(result, args.site))
    return 0


if __name__ == "__main__":
    sys.exit(main())
