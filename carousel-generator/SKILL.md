---
name: carousel-generator
description: Generates Instagram/LinkedIn/Stories carousels as editable HTML files, then exports each slide as a JPG or PNG via Playwright. Use this skill whenever the user asks for: a carousel, a multi-slide post, a visual thread, "slides for Instagram", "carrossel", "post visual", turning a newsletter/script/article into social media slides, or any content that needs to be broken into sequential visual cards. Works with any brand identity — provided explicitly (Mode A), extracted from a reference file or URL (Mode B), or auto-proposed from the content tone (Mode C). The HTML is always the editable source of truth; images are regenerated on each export. When the user asks to edit a carousel, update the HTML and re-export — never edit the JPGs directly. ALWAYS use this skill for carousel requests, even if the user doesn't say "carousel" — phrases like "slides para Instagram", "carrossel", "post de múltiplos slides", or "quero criar um visual" are enough to trigger it.
argument-hint: [content-path | topic | URL]
allowed-tools: Read, Write, Edit, Glob, Bash, AskUserQuestion, WebFetch
---

# Carousel Generator

Generate Instagram/LinkedIn carousels as **editable HTML** + **JPG/PNG export**.

The HTML is always the source of truth. JPGs are derivatives, always regeneratable.

---

## Workflow — 5 phases (follow in order)

### Phase 1 — Brand Resolution

Determine the visual identity. Check: does a `brand-configs/<slug>.brand.json` already exist in this skill's directory?

- **Yes**: Load it. Confirm with the user: "Usar brand config `<name>`? [sim/não]"
- **No**: Ask via `AskUserQuestion`:
  - "Você tem a identidade visual definida? Como prefere configurar?"
  - Options: "Tenho referência (manual/site/arquivo)", "Vou informar cores e fontes", "Pode propor a partir do conteúdo"

**Mode A — Explicit:**
Ask for: primary bg color, deep/dark bg color, accent color, muted fg color, on-dark fg color, display font, body font, mono font (optional), aspect ratio, footer handle/site, logo (path or describe). Save to `brand-configs/<slug>.brand.json`.

**Mode B — Extract from reference:**
Read the reference file/URL. Extract:
- Colors: look for CSS custom properties (`--color-*`, `var(--*)`) or repeated hex values. Identify bg, dark bg, accent, text colors.
- Fonts: `font-family` declarations or Google Fonts `<link>` tags.
- Voice/tone: read any copy and infer register (formal/editorial/playful/technical).
- If the reference has a stylesheet import, read it too.
Save extracted config to `brand-configs/<slug>.brand.json`. If something is ambiguous, ask.

**Mode C — Auto-propose:**
Read the content. Classify tone (editorial, playful, corporate, lifestyle, technical). Propose 2 palettes + 2 font combos with AskUserQuestion previews. User chooses; save to brand config.

### Phase 2 — Content Intake

Read the content from the provided path/URL/text.
Summarize in 3 bullets: **theme**, **target audience**, **angle / hook**.
Identify existing hook and CTA if present.

### Phase 3 — Outline Approval

Produce a table: `# | Pattern | Content (25 words max) | Background | Notes`

Show it and ask: "Aprovado? Posso gerar o HTML?"

Do NOT generate HTML before approval.

Slide count guidelines:
- Dense carousels (educational, B2B): 8–12 slides
- Synthetic carousels (listicles, quick hits): 5–7 slides
- Story format: 4–6 slides

### Phase 4 — HTML Generation

1. Choose template: `editorial` for formal/B2B, `default` for neutral, `bold` for lifestyle/high-contrast. Ask if unclear.
2. Read `references/slide-patterns.md` for HTML snippets for each pattern.
3. Read `references/aspect-ratios.md` for the chosen ratio's dimensions.
4. Copy the base template from `templates/<chosen>.html`.
5. Inject brand config as CSS custom properties in a `<style>` block at the top of `<body>`.
6. Write one `<section class="slide">` per row in the approved outline.
7. Save as `<output-dir>/<slug>.html` (default: `./carousels/<slug>.html`).

**CSS injection pattern** (inside `<style>` after template's existing styles):
```css
:root {
  --c-bg: <brand.colors.bg>;
  --c-bg-alt: <brand.colors.bg_alt>;
  --c-bg-deep: <brand.colors.bg_deep>;
  --c-fg: <brand.colors.fg>;
  --c-fg-muted: <brand.colors.fg_muted>;
  --c-fg-deep: <brand.colors.fg_on_deep>;
  --c-accent: <brand.colors.accent>;
  --c-accent-dim: <brand.colors.accent_alt ?? darken(accent)>;
  --f-display: <brand.fonts.display>;
  --f-body: <brand.fonts.body>;
  --f-mono: <brand.fonts.mono ?? monospace>;
  --slide-w: <aspect.width>px;
  --slide-h: <aspect.height>px;
}
```

If brand.extras.stylesheet_imports is set, add `<link rel="stylesheet">` tags before the style block (using the path from the config). Same for script_imports.

### Phase 5 — Export

Run:
```bash
python ~/.claude/skills/carousel-generator/scripts/render.py <html-path>
```

This produces `<html-dir>/exports/<slug>/01.jpg … NN.jpg` (default JPG q=92, @2x).
Use `--png` for lossless. Use `--quality 85` for smaller files.

Report the export path and slide count.

**Prerequisite check**: Before running, verify Playwright is installed:
```bash
python -c "from playwright.async_api import async_playwright; print('ok')" 2>&1
```
If it fails, run: `pip install playwright && playwright install chromium`
If install isn't possible, tell the user to do it, and offer the manual fallback: open the HTML in Chrome → Cmd+P → Save as PDF (1 page per slide).

---

## Iteration workflow

When the user asks to change something after export:

1. Edit **only the HTML** (use `Edit` tool — never rewrite from scratch unless content changes entirely).
2. Re-run `render.py` on the same file.
3. JPGs are overwritten with the same filenames (continuity for drag-and-drop uploaders).
4. Report: "Slide(s) X updated. Same export path."

---

## Hard rules

- **HTML is source of truth.** Never tell the user to edit the JPG.
- **Brand config persists.** Once saved, reuse across sessions without asking again. Update only when user requests a change.
- **Compliance validation**: If the brand config has `compliance_notes` or `vocabulary_avoid`, validate copy before writing slides. For Brazilian OAB context: no result guarantees, no victory promises, always cite legal foundation when making legal claims.
- **Min font sizes in slides**: title ≥ 56px, body ≥ 22px (at 1080×1350). If the content is too long to fit at minimum sizes, split the slide or trim copy.
- **Every carousel ends with a CTA slide** (even if minimal: "salva", "comenta", "segue").
- **Attribution**: keep the brand handle/footer on every slide if the brand config has `footer.handle`.
- **Mode B extraction never invents**: if a color or font isn't found in the reference, ask. Don't guess.

---

## Reference files

- `references/slide-patterns.md` — 10 HTML patterns (hook-deep, hook-light, qualification, problem, villain-loop, turn-authority, numeral-quote, examples-grid, voice-pair, cta-double). Read for snippets.
- `references/brand-config-schema.md` — Full JSON schema + TriboTax example. Read when creating or explaining brand configs.
- `references/aspect-ratios.md` — Dimensions for IG portrait, IG square, LinkedIn, story. Read during Phase 4.
- `references/extraction-guide.md` — How to extract brand tokens from CSS, HTML, PDF. Read during Mode B.
- `references/auto-brand-guide.md` — Palette + font heuristics per tone category. Read during Mode C.
- `templates/_slide-patterns.css` — Shared CSS for all patterns. Already linked in each template.
