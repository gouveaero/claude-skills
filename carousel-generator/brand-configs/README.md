# Brand Configs

One `.brand.json` file per brand. The skill loads these automatically by slug.

## Naming convention

```
<slug>.brand.json
```

Examples:
- `tribotax.brand.json`
- `my-saas.brand.json`
- `client-fashion.brand.json`

## How a brand config gets created

| Mode | How |
|---|---|
| **A — Explicit** | You provide palette, fonts, voice directly. Skill asks guided questions and saves the file. |
| **B — Extracted** | You point to a reference (HTML manual, website URL, PDF). Skill reads it and extracts tokens. |
| **C — Auto** | You only give content. Skill classifies the tone and proposes 2 palette options for you to pick. |

## How to use a saved config

Pass `--brand <slug>` when invoking the skill:

```
/carousel-generator my-content.md --brand tribotax
```

Or let the skill detect it automatically if you only have one brand config saved.

## Fields reference

See `references/brand-config-schema.md` for the full schema with all fields documented.

## Starting from scratch

Copy `_example.brand.json`, rename it to `<your-slug>.brand.json`, and fill in the values.
