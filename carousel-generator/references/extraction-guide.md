# Mode B — Extraction Guide

How to extract brand tokens from a reference file (HTML manual, website, PDF).

---

## From an HTML file (manual de marca, landing page)

1. **Colors**: look for `:root { --color-*: #xxx }` or `var(--*)` usage patterns. Identify:
   - Most-used light background → `bg`
   - Second lightest → `bg_alt`
   - Darkest / near-black → `bg_deep`
   - Main text color → `fg`
   - Muted/secondary text → `fg_muted`
   - Text on dark backgrounds → `fg_on_deep`
   - Accent / highlight / CTA → `accent`
   - Lighter/dimmer accent → `accent_alt`

2. **Fonts**: find `font-family` declarations or `<link>` tags pointing to Google Fonts. Classify:
   - Serif or display font → `display`
   - Sans-serif body font → `body`
   - Monospace if present → `mono`

3. **Logo**: look for `<symbol>` in SVG defs, or `<img>` with the brand name/logo. If inline SVG, extract the `<symbol>` block. If path, note the path.

4. **Voice/tone**: read headings and copy. Is it: formal, editorial, technical, playful, lifestyle? Note any compliance language.

5. **Footer handle/website**: look in the HTML footer or metadata.

### TriboTax example (manual-marca.html + tokens.css)

From `tokens.css`:
```
--clay-50:   #F6F1E8  → bg
--clay-100:  #EFE7D8  → bg_alt
--forest-900:#14251D  → bg_deep
--ink-900:   #121210  → fg
--ink-500:   #55544E  → fg_muted
             #E7DEC9  → fg_on_deep (from --fg-on-deep)
--copper-500:#8F3A2E  → accent
--copper-300:#C07D6E  → accent_alt
```

From `manual-marca.html`:
```
--f-display: "Cormorant Garamond" → fonts.display
--f-body:    "Inter Tight"        → fonts.body
--f-mono:    "JetBrains Mono"     → fonts.mono
Google Fonts link present         → google_fonts_url
<symbol id="tt-mark">             → logo.kind = "svg-symbol", src = "#tt-mark"
```

Voice (from copy): editorial, sóbrio, técnico, confiante. Português. Sem superlativos. OAB-compliant.

---

## From a website URL (WebFetch)

1. Fetch the URL.
2. Look for inline `<style>` blocks or linked CSS files.
3. Follow the same CSS variable extraction steps above.
4. If the CSS is in an external file (e.g. `styles.css`), try fetching it directly.

---

## From a PDF

1. Use `Read` with `pages: "1-5"` to read the manual pages.
2. Look for color swatches listed as hex codes (e.g. "#003366" or "RGB: 0, 51, 102").
3. Fonts are usually named explicitly ("Utiliza-se Montserrat Regular para corpo de texto").
4. Logo: PDFs don't yield SVG directly — note the logo description. Set `logo.kind = "img"` and `logo.src = ""` (user will provide later).

---

## When data is ambiguous

- If you can't determine `bg_deep` (no dark background in reference), use a very dark desaturated version of the accent color, or ask.
- If only one font is identified, use it for both `display` and `body`.
- If `fg_on_deep` isn't explicit, use `#E5DDD0` (warm off-white) as default — good with most dark backgrounds.
- Always confirm extracted config with the user before saving if anything was assumed.
