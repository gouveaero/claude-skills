---
name: slidev-presentation
description: Create sophisticated animated technical presentations using Slidev with a curated library of custom Vue components (CodeReveal, StatNumber, ArchitectureFlow, TerminalDemo, QuoteReveal). Use when the user wants to build a technical talk, developer conference keynote, or cinematic dev-focused slide deck with code, diagrams, and advanced animations. Follows a 4-phase flow: intake → discovery → outline approval → generation with live preview.
argument-hint: [file-path | topic-description]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion
---

# Slidev Technical Presentation — Cinematic Dev Decks

## Goal
Produce a sophisticated, animated technical presentation as a Slidev project. The final deliverable is a folder containing `slides.md`, a pre-wired custom component library, and a running dev preview. The user can also export to PDF, static SPA, or video.

## Why Slidev (for this skill)
- **Markdown-first** — ideal for Claude to author and iterate.
- **Animations** — built-in `v-click`, `v-motion`, view-transition API, Shiki Magic Move.
- **Technical native** — Shiki highlighting, Monaco live editor, Mermaid, KaTeX, embeds.
- **Extensible** — custom Vue components auto-register. Our library ships with 5 sophisticated components.
- **Reproducible** — pure text files, version-controllable.

## Inputs
- `$ARGUMENTS` — optional: a file path (markdown, transcript, article) OR a short topic description. If omitted, ask.

---

## The 4 phases (MANDATORY order)

Detailed specs in [WORKFLOW.md](WORKFLOW.md). Component API reference in [COMPONENTS.md](COMPONENTS.md).

### Phase 1 — Intake
Read any attached file / explore any referenced folder. Summarize in 3–4 bullets what you understood (domain, tone, existing structure, key artifacts). This is your anchor for the rest.

### Phase 2 — Discovery
Ask the clarifying questions from WORKFLOW.md. Ask ONLY what you can't infer confidently — batch everything in a single AskUserQuestion call when possible.

### Phase 3 — Outline approval
Produce a slide-by-slide plan as a table: `#`, `Título`, `Propósito`, `Componente sugerido`. End with an explicit question: **"Aprova esse outline? Posso gerar a apresentação?"** — do NOT proceed without a clear yes.

### Phase 4 — Generation
1. Confirm target folder (default: `./presentation/` relative to pwd).
2. Copy `templates/*` into the target folder.
3. Write `slides.md` by expanding the approved outline — use the custom components where they fit (see COMPONENTS.md).
4. Update `package.json` name field with the deck title (kebab-case).
5. Run `npm install` (background).
6. When install finishes, run `npm run dev` and report the local URL.
7. Tell the user the export commands: `npm run export` (PDF), `npm run build` (SPA), `npm run export -- --format video` (video).

---

## Hard rules

- **NEVER skip** Discovery and Outline approval. Even if the user's prompt is rich, confirm before generating.
- **ALWAYS Slidev syntax** — `slides.md` uses Slidev frontmatter, slide separators (`---`), layouts, and directives. Not generic markdown.
- **Language**: default to Portuguese. Match the input language otherwise.
- **One idea per slide.** Use `v-click` / `<v-clicks>` to reveal progressively. Reject slide walls of text.
- **Prefer custom components** over plain markdown when content benefits from animation:
  - Code walkthrough → `<CodeReveal>`
  - Big numbers/metrics → `<StatNumber>`
  - System diagrams → `<ArchitectureFlow>`
  - CLI demos → `<TerminalDemo>`
  - Opening/closing quotes → `<QuoteReveal>`
- **Transitions**: use `view-transition` globally in frontmatter for Magic-Move-style morphing. Per-slide `transition: fade-out` or `slide-up` where it adds intent.
- **Typography**: Inter for sans, JetBrains Mono for code (set in frontmatter `fonts`).
- **Themes**: default to `seriph` unless the user asked for something different.

## Component library (in `templates/components/`)

| Component | Use for |
|-----------|---------|
| `CodeReveal` | Step-by-step code walkthrough with highlighted lines + side notes |
| `StatNumber` | Animated counter (0 → target) with prefix/suffix/label |
| `ArchitectureFlow` | SVG architecture diagrams revealed node-by-node on click |
| `TerminalDemo` | Simulated terminal session with typing animation |
| `QuoteReveal` | Word-by-word staggered quote reveal |

Full API and examples in COMPONENTS.md.

## Output at end of Phase 4

Reply with:
1. Target folder path.
2. Dev server URL.
3. Total slide count.
4. Export commands.
5. A short "what to tweak next" prompt (e.g. "quer ajustar o ritmo de algum slide?").
