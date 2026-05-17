---
name: canva-presentation
description: Create beautiful, modern Canva presentations from a markdown file or folder. Handles pitches, educational decks, internal reports, and custom formats in PT/EN with 4 visual styles (minimalist, vibrant, corporate, editorial). Always delivers a design in Canva plus an Animation Playbook with per-slide Canva animation instructions. Use when the user wants to create slides, a deck, a pitch, or a presentation.
argument-hint: [markdown-path | folder-path]
allowed-tools: Read, Glob, Grep, Write, Bash, AskUserQuestion, mcp__claude_ai_Canva__request-outline-review, mcp__claude_ai_Canva__generate-design-structured, mcp__claude_ai_Canva__start-editing-transaction, mcp__claude_ai_Canva__perform-editing-operations, mcp__claude_ai_Canva__commit-editing-transaction, mcp__claude_ai_Canva__cancel-editing-transaction, mcp__claude_ai_Canva__list-brand-kits, mcp__claude_ai_Canva__get-design-thumbnail, mcp__claude_ai_Canva__get-design
---

# Canva Presentation — Beautiful decks with Animation Playbook

## Goal
Create a polished Canva presentation and deliver an **Animation Playbook** the user applies in Canva UI to get sophisticated, "wow-factor" motion.

**Why the playbook:** the Canva MCP has no animation API. We design FOR animation and hand off precise per-slide instructions. The playbook combines Canva's native element presets (Rise, Pan, Fade, Block, Breathe, Drift, Tectonic, Neon, Stomp, Slide, Roll + page transitions) with **Canva Pro advanced motion** (Motion Path Animator, Magic Animate, custom timeline keyframes, text-write effects, animated stickers/elements) to achieve a high level of sophistication.

## Inputs
- `$ARGUMENTS` — optional path to a markdown file OR folder. If omitted, ask.
- The user picks 4 things upfront (see Step 1).

---

## Workflow

### Step 1 — Collect the 4 choices

Use **AskUserQuestion** to ask all four in a single call:

1. **Tipo de apresentação / Presentation type:** Pitch comercial • Educacional/aula • Relatório interno • Outro (descrever)
2. **Idioma / Language:** Português • English
3. **Estilo visual / Visual style:** Minimalista (Apple-like) • Colorido/vibrante • Corporativo sóbrio • Editorial
4. **Fonte / Source:** Arquivo markdown (path) • Pasta atual (analisar arquivos) • Outline pronto (colar)

Ask in the user's language. If `$ARGUMENTS` was provided and is a valid path, skip question 4 and infer the source.

**Also check brand kits once:** call `list-brand-kits`. If ≥1 exists, ask the user if they want to apply one (by name). If auth fails, note it and proceed without.

---

### Step 2 — Ingest content

**If markdown file:** `Read` it fully. If >2000 lines, read in chunks.

**If folder:** `Glob` for `**/*.{md,txt,pdf,docx}` first. Prioritize:
- `README.md`, `CLAUDE.md`, files with "brief", "proposta", "proposal", "estrategia", "plan" in the name
- Read top 5-10 most relevant files (by filename signal + recency)
- If >10 candidates, ask the user which to prioritize

**If outline pasted:** skip to Step 3 with that outline.

Never dump raw file content back to the user. Synthesize.

---

### Step 3 — Propose outline in plain text (iterate FIRST)

**Critical:** do NOT call `request-outline-review` yet. Show the outline as plain markdown so the user can iterate cheaply.

Length defaults by type:
- Pitch: 8-12 slides
- Educacional/aula: 12-20 slides (balanced or comprehensive)
- Relatório interno: 10-15 slides
- Outro: propose based on content density

Outline format to show the user:
```
### Outline proposta ({N} slides)

1. **[Título]** — [1 frase do que tem no slide]
2. **[Título]** — [1 frase]
...
```

Then ask: *"Esse outline está bom ou quer ajustes (adicionar/remover/reordenar slides, mudar foco)?"*

**Iterate in plain text until user approves explicitly.** Typical iterations: reorder, merge slides, split dense slides, change emphasis.

---

### Step 4 — Canva outline review (MCP requirement)

Once user approves the plain-text outline, call `request-outline-review` with:
- `topic`: 1-line description of the deck
- `pages`: array of `{title, description}` — match the approved outline exactly
- `style`: mapped from user's choice (see Style Mapping below)
- `audience`: inferred or asked (pitch → "investors" or "prospects"; aula → "students" or "team"; relatório → "executives" or "team")
- `length`: "short" (≤5), "balanced" (5-15), or "comprehensive" (15+)
- `brand_kit_id` + `brand_kit_name`: if user chose a brand kit

The widget appears in Canva. **Wait for user approval in the widget.** If they request changes in chat, update the outline and call `request-outline-review` again. Never call `generate-design-structured` without widget approval.

#### Style mapping (user choice → Canva `style`)

| User choice | Canva style param |
|---|---|
| Minimalista (Apple-like) | `minimalist` |
| Colorido/vibrante | `playful` |
| Corporativo sóbrio | Custom string: `"corporate, clean, navy and light grey, subtle accents, serif headings with sans-serif body"` |
| Editorial | `modular` |

---

### Step 5 — Generate the design

After widget approval, call `generate-design-structured` with the same params. It returns a design ID and preview thumbnails. Show the thumbnails to the user.

---

### Step 6 — Polish pass (typography + hierarchy)

Call `start-editing-transaction` → inspect pages → `perform-editing-operations` → `commit-editing-transaction`.

**What to polish (only if it improves clarity — don't over-edit):**
- **Title slide:** ensure the hook is ≤8 words. If too long, shorten.
- **Type hierarchy:** body text font_size 18-24, headings 36-60, hero numbers 80-140.
- **Color accents:** if brand kit applied, reinforce accent color on key numbers/pull-quotes.
- **List formatting:** bullets use `list_marker: disc` or `circle`; nested lists use `list_level: 2` with `lower-alpha`.
- **Line height:** body 1.3-1.5, headings 1.05-1.15.
- **No orphan words** on headings — rephrase if a single word drops to a new line.

Skip polish entirely if the generated design already looks clean. Don't touch responsive pages beyond allowed ops (`update_title`, `update_fill`, `delete_element`, `find_and_replace_text`).

**Always show user the preview thumbnails before and after.** Ask approval before `commit-editing-transaction`.

---

### Step 7 — Deliver the Animation Playbook (basic + advanced tiers)

The playbook has **two tiers**. Always deliver Tier 1. Deliver Tier 2 when the user asks for sophistication, "wow factor", or when the deck is a high-stakes pitch/keynote.

**Tier 1 — Native element presets + page transitions** (universal, works in Free and Pro).
Element animations: Rise, Pan, Fade, Block, Breathe, Drift, Tectonic, Neon, Scrapbook, Stomp, Slide, Roll, Pop, Bounce, Baseline, Skate, Shift. Page transitions: None, Dissolve, Flow, Slide, Block, Stack, Wipe, Freefall, Line, Colour Wipe.

**Tier 2 — Canva Pro advanced motion** (Pro subscription required; flag this once at the top of the playbook). Four capabilities:

1. **Motion Path Animator** — draw a custom path that any element follows during entrance/on-slide. Use for:
   - Step-by-step flows where a marker/dot travels between nodes (Slide 9 lawyer flow archetype)
   - Data points that "land" on a chart from an origin (map pin flying onto a map)
   - Narrative elements that follow a curve to guide the eye (arrow from problem → solution)
   - How to specify in the playbook: *"Motion Path: {element} follows path from {A} to {B}, duration {X}s, easing ease-in-out"*

2. **Magic Animate** — one-click whole-slide animation that Canva's AI choreographs from slide structure. Use for:
   - Establishing a baseline animation pass on content-heavy slides when stagger+preset would be tedious
   - Editorial/cinematic slides where the exact choreography is less important than overall polish
   - How to specify: *"Magic Animate: On (Slow). Override individual element presets below if they conflict."*

3. **Text-write / typewriter / letter-by-letter effects** — text reveals progressively as if being typed or handwritten. Use for:
   - Key thesis titles (the "one-sentence payoff" slide)
   - Quotes or punchlines where pacing = impact
   - Formulas, code snippets, or rules that benefit from "watch it being constructed"
   - How to specify: *"Text write-on: letter-by-letter, speed 40 chars/s"* or *"Word-by-word reveal, 0.15s per word"*
   - Implementation in Canva: apply **Typewriter** text effect (Text menu → Effects → Animate text → Typewriter), OR use "Rise" with per-character stagger via splitting the text into separate text boxes (heavier but more controllable).

4. **Custom keyframe animations (timeline panel)** — set entrance, mid-slide emphasis, and exit per element with keyframes for position/scale/rotation/opacity. Use for:
   - Animated counters on hero numbers (scale 0.9 → 1.0 while fading in, then brief pulse at 1.05 → 1.0 for emphasis)
   - Dashboard KPIs that "count up" (approximate via quick opacity-layer stacking: show "0 →" then replace with final number with a 0.4s crossfade)
   - Diagram nodes that pulse when highlighted during narration
   - How to specify: *"Keyframe: entrance 0-0.5s (opacity 0→1, scale 0.95→1.0), emphasis 0.5-0.7s (scale 1.0→1.05→1.0)"*

**Animated decorative elements** (Free, but high-impact when used sparingly):
- **Breathe** (continuous) on background shapes, brand marks, or the accent circle behind a hero number — adds subtle "alive" quality.
- **Animated stickers / Elements** — Canva's library has pre-animated icons (pulsing dots, flowing arrows, rotating gears). Search in Elements → filter "Animated". One per slide max.
- **Animated charts** — when generating a chart, enable "Animate chart" in chart settings (Wipe bottom-up = bar reveal; Fade = line draw).

---

### Tier 3 — Ambient & continuous motion (the "alive" layer)

Tier 1 and Tier 2 are still **entrance** animations — they happen once and freeze. **A deck that feels ALIVE needs motion that persists throughout each slide.** Tier 3 is what converts a "polished static" deck into a "living environment".

**Mental model shift:** stop choreographing "how elements arrive". Start designing "what keeps moving while the presenter talks". If you paused every slide 10s after entrance and nothing was moving, the deck is dead.

Four capabilities, stacked per slide:

1. **Ambient background video loop (universal).** Upload a dark, subtle MP4 loop (particles, grain, slow gradient mesh, soft light rays) and place it as the lowest layer on every slide at 10-25% opacity. This is the single biggest lever — it converts "flat slide" into "depth". Sources: Pexels, Pixabay, Mixkit (all free, direct MP4 URLs). Use `upload-asset-from-url` then `insert_fill` with `asset_type: "video"` on each page. Keep file small (<5MB, 720p) so it loops seamlessly.

2. **Breathe stagger pattern (continuous loops on every amber/accent element).** Don't apply Breathe to just 1-2 elements — apply to ALL shapes/accents, each with a different start phase (Canva handles the loop timing; you stagger by starting each element's animation at a different moment during initial page load). The deck now pulses polyrhythmically — never a moment of total stillness.

3. **Looping Motion Path (continuous, not one-shot).** When using Motion Path, set `Loop: on`. The element repeats its trajectory infinitely. Stack MULTIPLE elements on the same path at different start times to simulate a particle stream / data flow (essential for architecture/flow diagrams).

4. **Video/Lottie hero assets on flagship slides.** For 2-3 key slides, replace static illustrations with animated equivalents: neural network diagrams with firing nodes, data flow visualizations, animated icon sets. Canva Pro supports MP4/WebM uploads. For Lottie, find the MP4 export (LottieFiles exports to MP4) — the MCP can only insert video/image, not raw .json Lottie.

**Layering rule:** a "living" slide should have AT LEAST 2 continuous motion sources active simultaneously — e.g., ambient video background (10% opacity) + Breathe on the amber sidebar = 2 independent rhythms = feels alive. Add a third (motion path loop, typewriter on trigger, animated sticker) on flagship slides.

**Visibility rule:** ambient motion must never fight readability. Background video opacity ≤25%. Breathe scale delta ≤5% (1.00 ↔ 1.05). Motion path loops use small accent elements (≤24px), never hero content. If the audience notices motion before they notice the content, it failed.

**Trade-off:** Tier 3 demands extra prep — sourcing MP4s, more upload operations, careful opacity/layering. Worth it for keynote/pitch. Skip entirely for corporate reports (too much motion = looks like a TV ad, not a serious brief).

**Choose tier per deck:**
- Corporate report → Tier 1 only (no Magic Animate, no typewriter — stay conservative).
- Educational → Tier 1 + Motion Path on flows/processes if content has them.
- Pitch/keynote → Tier 1 + all Tier 2 capabilities (judicious: motion path on 1-2 slides, typewriter on 1 thesis slide, keyframe counters on hero stats, Magic Animate off — pick manually per slide).
- Editorial → Tier 1 + Magic Animate as baseline, plus typewriter on pull quotes.

Load [animation-playbook.md](animation-playbook.md) for the master preset matching the user's visual style. Then write a **custom playbook file** to the current working directory:

Path: `./apresentacao-{YYYY-MM-DD}-animation-playbook.md` (or `.presentation-{date}-animation-playbook.md` if EN)

Content structure:
```markdown
# Animation Playbook — {Deck Title}

**Design:** [link from get-design]
**Estilo:** {style}
**Preset mestre:** {preset name from animation-playbook.md}
**Tier 2 (Canva Pro):** {sim/não — listar capacidades usadas: Motion Path, Typewriter, Keyframe counters, Magic Animate}

## Como aplicar no Canva (5-12 min)
1. Abra o design no link acima.
2. **Tier 1 (element presets):** para cada slide, selecione os elementos na ordem listada → "Animate" → preset indicado → velocidade.
3. **Tier 2 (Pro):**
   - **Motion Path:** selecione o elemento → "Animate" → "Create an animation" (Motion Path) → desenhe o caminho na tela.
   - **Typewriter:** selecione o texto → menu "Effects" → "Animate" → "Typewriter" → ajuste a velocidade.
   - **Keyframe:** selecione o elemento → "Animate" → "Create an animation" → abra o timeline e adicione keyframes de posição/escala/opacidade.
   - **Magic Animate:** apenas se indicado — "Animate" → "Magic Animate" no painel da página.
4. **Page transitions:** "..." no canto superior da página → "Transitions" → preset → velocidade.

---

## Slide 1 — {title}
- **Page transition:** {e.g. Dissolve 0.5s}
- **Tier 1 elements (order of animation):**
  1. {element} → {preset} ({timing})
  2. ...
- **Tier 2 (if applicable):**
  - **Motion Path:** {element} follows path {description}, {duration}, {easing}
  - **Typewriter:** {text element}, {speed}
  - **Keyframe:** {element}, {0s-Xs: property change}

## Slide 2 — {title}
...
```

For each slide, pick animations from the master preset. Use element order that matches reading flow (title → subtitle → body → visual). Reserve Tier 2 for the 2-4 highest-impact slides (title, hero numbers, key flow/diagram, closing) — not every slide.

**Finally, send the user:**
1. The Canva design link
2. The path to the playbook file
3. A 2-sentence summary of what was generated

---

## Philosophy — designing FOR animation

Good animation starts with good structure. When iterating the outline in Step 3:
- **One big idea per slide** — multiple ideas = muddled animation
- **Separate elements for staged reveal** — a "3 pillars" slide should have 3 distinct elements, not one combined block
- **Hero numbers alone** — big stats deserve their own slide; they animate beautifully (and unlock keyframe-counter effects)
- **Contrast slides** — alternate dense and sparse slides so animation has breathing room
- **Plan the "motion moments"** — pick 2-4 slides per deck that will carry advanced motion (title/thesis typewriter, hero-number counter, flow with motion path, closing reveal). The rest stay clean Tier 1. Sophistication comes from *contrast*: a single standout motion beat on a slow-paced slide lands harder than motion everywhere.
- **Structure flows for motion path** — any "step 1 → step 2 → step 3" slide should have those steps laid out as a physical path on the canvas (horizontal timeline, diagonal cascade, circular loop). This enables a marker dot to travel the path during animation.
- **Structure diagrams for progressive reveal** — architecture/diagram slides work best when nodes can be revealed in narrative order (source → transform → destination), each with its own connecting arrow that draws in after. Avoid one giant locked image.

### Tier 2 / Tier 3 quick-reference — when to use each

| Capability | Tier | Use on | Skip on |
|---|---|---|---|
| **Ambient video background** | 3 | Every slide of a pitch/keynote deck, 10-25% opacity | Corporate/report decks |
| **Breathe stagger (all accents)** | 3 | Every amber/accent shape, phases offset | Minimal decks with only 1 accent |
| **Looping Motion Path + particle stream** | 3 | Architecture, flows, maps — loop=on with multiple stacked dots | One-shot processes |
| **Video/MP4 hero asset** | 3 | 2-3 flagship slides max (cover, architecture, closing) | Text-driven slides |
| **Motion Path (single pass)** | 2 | Step-by-step reveal during narration | Continuous processes (use loop instead) |
| **Typewriter** | 2 | Thesis statement, killer quote, rule/formula | Body text, short titles |
| **Keyframe counter** | 2 | Hero numbers, KPIs | Text-heavy slides |
| **Magic Animate** | 2 | Editorial as baseline; rescue cluttered slides | Pitch/corporate |
| **Animated sticker** | 2 | A single accent per deck | Fights brand tone |
| **Breathe (single element)** | 1 | Not enough on its own — use stagger pattern (Tier 3) | — |

---

## Edge cases

- **Canva auth missing:** if any Canva MCP call fails with auth error, tell the user to authenticate via the Canva connector and pause.
- **Folder has 50+ files:** don't read all — ask user to narrow down or point to 1-2 key docs.
- **Markdown has no clear structure:** propose an outline based on implicit sections (H2/H3 as slide boundaries) and flag that it's a best-guess.
- **User wants to skip outline review:** not possible — MCP requires the widget approval. Explain.
- **User rejects generated design entirely:** offer to regenerate with a different `style` param (e.g., switch `minimalist` → `elegant`) rather than manual editing.
- **Responsive pages:** `perform-editing-operations` only allows `update_title`, `update_fill`, `delete_element`, `find_and_replace_text` on responsive pages. Respect this.
- **Idioma misto:** keep content strictly in the chosen language. If source mixes languages, translate on the fly.

---

## What NOT to do

- Don't call `generate-design-structured` without widget approval — the MCP will reject.
- Don't promise real-time animations — we only produce the playbook; user applies it.
- Don't batch tiny edits; group `perform-editing-operations` operations.
- Don't auto-commit the editing transaction without showing a preview.
- Don't create new helper files beyond the playbook unless the user asks.
