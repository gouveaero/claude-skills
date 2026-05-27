#!/usr/bin/env python3
"""
render.py — Carousel Generator export script
Renders each <section class="slide"> in an HTML file as a JPG (or PNG).

Usage:
    python render.py <html-path> [--png] [--quality 92] [--dpr 2] [--out <dir>]

Requirements:
    pip install playwright
    playwright install chromium

Output:
    <html-dir>/exports/<html-stem>/01.jpg ... NN.jpg  (default)
    <html-dir>/exports/<html-stem>/01.png ... NN.png  (--png)
"""

import sys
import asyncio
import pathlib
import argparse


async def render(html_path: pathlib.Path, fmt: str, quality: int, dpr: int, out_dir: pathlib.Path):
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("✗ Playwright not found. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    ext = "png" if fmt == "png" else "jpg"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Use device_scale_factor for @2x exports (2160×2700 at dpr=2 for 1080×1350 slides)
        ctx = await browser.new_context(device_scale_factor=dpr)
        page = await ctx.new_page()

        file_url = html_path.resolve().as_uri()
        await page.goto(file_url, wait_until="networkidle")

        # Force noscale on deck-stage if present (renders at authored size, not scaled-to-viewport)
        await page.evaluate("""
            const ds = document.querySelector('deck-stage');
            if (ds) {
                ds.setAttribute('noscale', '');
                // Show all slides for screenshot (deck-stage hides inactive ones)
                ds.querySelectorAll('section').forEach(s => {
                    s.style.visibility = 'visible';
                    s.style.opacity = '1';
                });
            }
        """)

        # Make all slides visible (the minimal viewer uses display:none on inactive)
        # Also reset the scale transform so each section screenshots at authored CSS size.
        await page.evaluate("""
            document.querySelectorAll('section.slide').forEach(s => {
                s.style.display = 'flex';
                s.style.visibility = 'visible';
                s.style.opacity = '1';
            });
            // Reset minimal-viewer scale transform — sections must be at 1:1 for correct export
            const wrapper = document.getElementById('slideWrapper');
            if (wrapper) {
                wrapper.style.transform = 'none';
                wrapper.style.marginLeft = '0';
                wrapper.style.marginTop = '0';
                wrapper.style.position = 'static';
            }
            // Hide the navigation UI
            const ui = document.getElementById('slideUi');
            if (ui) ui.style.display = 'none';
        """)

        # Wait for fonts to load
        await page.evaluate("document.fonts.ready")
        await page.wait_for_timeout(300)

        sections = await page.query_selector_all("section.slide")
        if not sections:
            print("✗ No <section class='slide'> elements found in the HTML.")
            await browser.close()
            sys.exit(1)

        for i, section in enumerate(sections, 1):
            if fmt == "png":
                img_bytes = await section.screenshot(type="png")
            else:
                img_bytes = await section.screenshot(type="jpeg", quality=quality)

            out_file = out_dir / f"{i:02d}.{ext}"
            out_file.write_bytes(img_bytes)
            print(f"  slide {i:02d}/{len(sections)} → {out_file.name}")

        await browser.close()

    count = len(sections) if sections else 0
    print(f"\n✓ {count} slides exported to: {out_dir}")
    return count


def main():
    ap = argparse.ArgumentParser(
        description="Export carousel HTML slides to JPG/PNG via Playwright."
    )
    ap.add_argument("html", help="Path to the carousel HTML file")
    ap.add_argument("--png", action="store_true", help="Export as PNG instead of JPG")
    ap.add_argument("--quality", type=int, default=92, help="JPEG quality 1-100 (default: 92)")
    ap.add_argument("--dpr", type=int, default=2, help="Device pixel ratio (default: 2 → @2x)")
    ap.add_argument("--out", help="Output directory (default: <html-dir>/exports/<html-stem>/)")
    args = ap.parse_args()

    html_path = pathlib.Path(args.html).resolve()
    if not html_path.exists():
        print(f"✗ File not found: {html_path}")
        sys.exit(1)

    if args.out:
        out_dir = pathlib.Path(args.out).resolve()
    else:
        out_dir = html_path.parent / "exports" / html_path.stem

    fmt = "png" if args.png else "jpg"
    asyncio.run(render(html_path, fmt, args.quality, args.dpr, out_dir))


if __name__ == "__main__":
    main()
