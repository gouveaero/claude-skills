# Brand Config Schema

Save one file per brand as `brand-configs/<slug>.brand.json`.

## Full schema

```json
{
  "name":        "Brand Name",
  "slug":        "brand-slug",
  "voice_tone":  "One-line tone descriptor: e.g. 'editorial, sóbrio, técnico, confiante; português; sem superlativos'",
  "vocabulary_use":   ["word1", "word2"],
  "vocabulary_avoid": ["word1", "word2"],
  "compliance_notes": "Optional: e.g. 'OAB: nunca prometer resultado, citar fundamento legal'",

  "colors": {
    "bg":        "#RRGGBB",
    "bg_alt":    "#RRGGBB",
    "bg_deep":   "#RRGGBB",
    "fg":        "#RRGGBB",
    "fg_muted":  "#RRGGBB",
    "fg_on_deep":"#RRGGBB",
    "accent":    "#RRGGBB",
    "accent_alt":"#RRGGBB"
  },

  "fonts": {
    "display": "Font Family Name, fallback, generic",
    "body":    "Font Family Name, fallback, generic",
    "mono":    "Font Family Name, fallback, monospace"
  },

  "google_fonts_url": "https://fonts.googleapis.com/css2?family=...",

  "aspect_ratio": "1080x1350",

  "logo": {
    "kind": "svg-inline | svg-symbol | img",
    "svg_inline": "<svg …>…</svg>",
    "src": "path/to/logo.svg or #symbol-id"
  },

  "footer": {
    "handle":  "@handle",
    "website": "website.com"
  },

  "extras": {
    "stylesheet_imports": [],
    "script_imports":     []
  }
}
```

## Required fields
`name`, `slug`, `colors.bg`, `colors.bg_deep`, `colors.accent`, `fonts.display`, `fonts.body`

## Optional fields
Everything else. If `google_fonts_url` is set, Phase 4 adds it as a `<link rel="stylesheet">` at the top of `<head>`. If `extras.stylesheet_imports` / `extras.script_imports` are set (paths or URLs), they are added as `<link>` / `<script>` tags.

---

## TriboTax example (already saved as `brand-configs/tribotax.brand.json`)

Key tokens:
- bg = `#F6F1E8` (argila quente)
- bg_deep = `#14251D` (floresta profunda)
- accent = `#8F3A2E` (terracota)
- display = Cormorant Garamond (serifa editorial)
- body = Inter Tight (sans neutra)
- mono = JetBrains Mono
- voice = editorial, sóbrio, técnico; português; OAB-compliant
- Template recommendation: `editorial`

---

## Mapping to CSS injection in Phase 4

| JSON key | CSS variable |
|---|---|
| `colors.bg` | `--c-bg` |
| `colors.bg_alt` | `--c-bg-alt` |
| `colors.bg_deep` | `--c-bg-deep` |
| `colors.fg` | `--c-fg` |
| `colors.fg_muted` | `--c-fg-muted` |
| `colors.fg_on_deep` | `--c-fg-deep` |
| `colors.accent` | `--c-accent` |
| `colors.accent_alt` | `--c-accent-dim` |
| `fonts.display` | `--f-display` |
| `fonts.body` | `--f-body` |
| `fonts.mono` | `--f-mono` |
| `aspect_ratio` width | `--slide-w` |
| `aspect_ratio` height | `--slide-h` |
