# Animation Master Presets

Four master presets, one per visual style. Each specifies: philosophy, page transition, per-slide-type animations, timing guidance. Use these to generate the per-deck Animation Playbook in Step 7 of SKILL.md.

Canva's available animation presets (as of 2026): **Rise, Pan, Fade, Block, Breathe, Drift, Tectonic, Neon, Scrapbook, Stomp, Slide, Roll, Pop, Bounce, Baseline, Skate, Shift**. Page transitions: **None, Dissolve, Flow, Slide, Block, Stack, Wipe, Freefall, Line, Colour Wipe**.

---

## Preset 1 — Minimalista (Apple-like)

**Philosophy:** restraint, precision, confidence. Nothing moves unless it adds meaning. Slow, graceful reveals.

**Page transition:** `Dissolve` at 0.5s (every page)

**Per-slide-type animations:**

| Slide type | Elements (in order) | Animation | Notes |
|---|---|---|---|
| Title/cover | Logo → Title → Subtitle | Fade (each) | 0.3s stagger between elements |
| Section divider | Section number → Section name | Rise → Fade | Number rises, name fades in after 0.4s |
| Single hero statement | Statement | Rise | Slow (1s). Let it breathe. |
| Hero number/stat | Number → Label | Rise → Fade | Number hits first, label 0.4s later |
| 3 bullet points | Each bullet | Fade | 0.5s stagger — slow, confident |
| Image + caption | Image → Caption | Fade → Fade | Image first, caption 0.3s later |
| Quote | Quotation marks → Quote → Attribution | Fade (all) | Slow stagger 0.5s |
| Closing/CTA | Primary CTA → Secondary | Rise → Fade | Strong focus on primary |

**Golden rule:** never use Stomp, Tectonic, Neon, Scrapbook, Pop, or Bounce. Those break the aesthetic.

---

## Preset 2 — Colorido/vibrante

**Philosophy:** energy, surprise, contrast. Animations alternate rhythm — fast, slow, fast. Delight-focused.

**Page transition:** `Flow` at 0.6s (alternate direction per page if possible)

**Per-slide-type animations:**

| Slide type | Elements (in order) | Animation | Notes |
|---|---|---|---|
| Title/cover | Title → Subtitle → Accent shape/emoji | Stomp → Pop → Bounce | Big entrance |
| Section divider | Section name → Background shape | Pop → Breathe | Shape breathes continuously |
| 3 bullet points | Each bullet | Pop (alternating directions) | 0.2s stagger, snappy |
| Hero number/stat | Number → Label | Tectonic → Pop | Number shakes in, label pops |
| Image + caption | Image → Caption | Bounce → Pop | Playful |
| Process/steps | Each step | Slide (left to right) | 0.3s stagger, energy builds |
| Quote | Quote → Attribution | Pop → Fade | |
| Closing/CTA | CTA button → Secondary elements | Stomp → Pop | Close with impact |

**Golden rule:** use Breathe sparingly on background elements (shapes, logos) for continuous subtle motion. Don't overuse or it becomes distracting.

---

## Preset 3 — Corporativo sóbrio

**Philosophy:** professionalism, clarity, zero distraction. Movement serves comprehension. Conservative, restrained.

**Page transition:** `Dissolve` at 0.4s (every page, no variation)

**Per-slide-type animations:**

| Slide type | Elements (in order) | Animation | Notes |
|---|---|---|---|
| Title/cover | Title → Subtitle → Date/author | Fade (all) | 0.3s stagger |
| Section divider | Section number → Section name | Fade → Fade | Simple, clean |
| Agenda/TOC | Each item | Fade | 0.2s stagger, quick |
| Bullet points | Each bullet | Block (from left) | 0.3s stagger — structured, hierarchical |
| Hero number/stat | Number → Label → Source/footnote | Fade → Fade → Fade | All fade, no theatrics |
| Chart/data | Chart container → Chart bars/lines | Fade → Wipe (bottom-up) | Wipe reveals data progressively |
| Table | Header row → Body rows | Fade → Block (top-down) | Row-by-row reveal |
| Quote | Quote → Attribution | Fade → Fade | |
| Closing/CTA | Recommendation → Next steps | Fade → Block | |

**Golden rule:** no Stomp, Tectonic, Neon, Bounce, Pop, Scrapbook. Keep everything below "obviously animated" — if the viewer notices the animation, it failed.

---

## Preset 4 — Editorial

**Philosophy:** narrative rhythm, cinematic pacing, magazine-like. Each slide is a frame in a visual story.

**Page transition:** `Wipe` at 0.7s (direction alternates: left→right, then right→left, etc.)

**Per-slide-type animations:**

| Slide type | Elements (in order) | Animation | Notes |
|---|---|---|---|
| Title/cover | Large title → Subtitle → Edition/issue number | Drift → Slide → Fade | Cinematic entrance |
| Section divider | Section label → Section title → Rule/line | Fade → Drift → Slide | |
| Full-bleed image + overlay text | Image → Overlay block → Text | Pan (slow) → Fade → Drift | Image pans continuously during slide |
| Pull quote | Quote marks → Quote → Attribution | Neon → Drift → Fade | Neon on quote marks for accent |
| 2-column spread | Left column → Right column | Slide (from each side) | Mirror animation |
| Hero stat | Number → Label → Context | Drift → Fade → Fade | |
| Process/timeline | Each step in sequence | Slide (horizontal) | 0.4s stagger — story rhythm |
| Closing | Final image → Closing line | Pan → Fade | Slow, meditative |

**Golden rule:** use Pan on any full-bleed image for continuous cinematic motion. Neon is reserved for pull quotes and accent typography — never body text.

---

## How to pick animations for a specific slide

When generating the per-deck Animation Playbook:

1. **Identify slide type** from its content (title / section / bullets / hero stat / image / quote / chart / closing).
2. **Look up the animation** in the matching preset table above.
3. **List elements in reading order** (eye travels top-left to bottom-right, or title→body→visual).
4. **Keep staggers consistent** per deck — don't mix 0.2s and 0.8s staggers arbitrarily.

If a slide doesn't match any category, default to:
- Minimalist/Corporate: Fade on everything, 0.3s stagger
- Vibrant: Pop on everything, 0.2s stagger
- Editorial: Drift on everything, 0.4s stagger

## Timing vocabulary

Canva lets you set animation speed: **Slow, Medium, Fast**. Map the rough timings used above:
- 0.2-0.3s → Fast
- 0.4-0.6s → Medium
- 0.7s+ → Slow

For page transitions, same mapping.

## Don't mix presets within a single deck

One visual style → one preset. Mixing presets (e.g., minimalist transitions with vibrant entrance animations) breaks cohesion. If the user wants hybrid, pick the closest single preset and note the tradeoff.

---

## Tier 2 — Canva Pro advanced motion patterns

Use these to create "wow factor" moments. **Rule: 2-4 Tier-2 moments per deck, max.** Sophistication = contrast. One motion beat on a calm slide hits harder than motion on every slide.

### A. Motion Path Animator — patterns by slide type

The Motion Path Animator lets you draw a custom trajectory that any element follows during animation (entrance or mid-slide). Access: select element → "Animate" → "Create an animation" → Motion Path tool.

| Slide type | Motion path recipe | Effect |
|---|---|---|
| **Step-by-step flow (3-5 steps)** | Draw a dot/marker. Path: horizontal line passing through each step's center, left → right. Duration: 2-3s. Easing: ease-in-out. Element pauses briefly (0.3s hold) on each step via keyframes. | Audience's eye physically follows the process — a marker "walks" the journey. |
| **Architecture / data flow diagram** | One small arrow or packet shape. Path: origin node → arrow curves through each transform → destination. Duration: 1.5-2.5s. Repeat (loop) if continuous process. | Shows data actually flowing through the pipeline, not just nodes sitting there. |
| **Before/after transformation** | The "before" element follows a curved path off-stage (exit path), "after" element follows a path in (entrance path). Duration: 0.8s each, chained. | Narrative handoff instead of a hard cut. |
| **Map / geographic** | Small pin or plane icon. Path: along the geography (city A → city B). Easing: ease-in-out, slight curve. | Classic travel/expansion storytelling. |
| **"Connecting the dots"** | Line element. Path: from concept A → concept B → concept C. Use the line's entrance path so it draws itself. | Synthesizes disparate ideas into a thesis, visually. |
| **Circular/loop narrative** | Element follows a full circle path and returns to origin. Duration: 3-4s, optional continuous loop. | Cycles, feedback loops, iterative processes. |

**Design requirement:** when using motion path, the slide layout must physically support the path. Lay out steps/nodes as a visible trajectory (horizontal timeline, diagonal cascade, perimeter of a circle) during Step 6 polish — don't add motion path to a grid layout and expect it to work.

### B. Typewriter / text-write effects

Access: select text → menu **Effects** → **Animate text** → **Typewriter** (or "Writer" / "Reveal by letter"). Alternatives: split text across multiple text boxes + stagger with Rise.

| Use case | Setup | Timing |
|---|---|---|
| Thesis statement / one-liner payoff | Typewriter on the full sentence | 40-50 chars/s — slow enough to read along |
| Formula or rule being "constructed" | Typewriter, with a pause (comma = longer pause) between clauses | 30 chars/s + 0.4s comma hold |
| Code snippet or query | Monospace font + Typewriter + cursor glyph | 50-70 chars/s |
| Pull quote | Word-by-word reveal (Rise preset on each word in separate text boxes) | 0.15-0.25s per word |
| Definition / "X is Y" reveal | Typewriter on just the predicate ("Y") while subject ("X is") appears instantly | 40 chars/s on predicate |

**Don't typewriter:** titles ≤3 words (no time to appreciate), body text in corporate decks (feels theatrical), anything the audience will read silently while you talk past it.

### C. Keyframe / custom timeline animations

Access: select element → "Animate" → "Create an animation" → open timeline panel → add keyframes for opacity/position/scale/rotation.

**Keyframe recipes:**

1. **Hero-number counter pulse** (approximates "counting up"):
   - 0-0.4s: opacity 0→1, scale 0.9→1.0 (entrance)
   - 0.4-0.55s: scale 1.0→1.08 (pulse peak)
   - 0.55-0.7s: scale 1.08→1.0 (settle)
   - Apply to the number text. Add a subtle drop shadow that intensifies during the pulse for extra weight.

2. **True counter effect** (if you need to see digits changing):
   - Stack 3-4 text boxes with intermediate values (e.g., "0 →" then "12 →" then "19"). Each one has opacity keyframes: box1 visible 0-0.3s, fades to 0 at 0.35s while box2 fades from 0 at 0.3s to 1 at 0.6s, etc. Final number settles at ~1.2s total.
   - Crude but works. The Typewriter effect on a number with commas can also simulate this.

3. **Card hover-lift (on reveal)**:
   - 0-0.5s: opacity 0→1, position y+30→y (slides up)
   - 0.5-0.65s: scale 1.0→1.03, shadow intensifies
   - 0.65-0.8s: scale 1.03→1.0 (settle)

4. **Diagram node emphasis pulse** (during narration):
   - Loop animation: scale 1.0 ↔ 1.05 every 1.5s, opacity steady at 1
   - Use Breathe preset as a zero-keyframe alternative if Pro not available.

5. **Connector-line draw-in** (between diagram nodes):
   - Create line with low opacity. Keyframes: 0-0.6s opacity 0→1, stroke dasharray animated to create "draw" effect (if available). Simpler alternative: Wipe preset on the line element, direction = along line axis.

### D. Magic Animate (whole-slide)

Access: Animate panel → Magic Animate. Canva AI choreographs the entire slide's elements automatically.

**When to turn on:**
- Editorial decks as a baseline layer (Preset 4)
- Content-heavy slides (8+ elements) where manually staggering would be tedious
- When the client wants "just make it animated" without caring about exact choreography

**When to turn OFF:**
- Pitch decks with specific narrative beats (override with explicit Tier 1 + Tier 2)
- Slides where you've already set motion path or typewriter (Magic Animate will conflict)
- Corporate reports (too showy)

**Pattern:** turn Magic Animate on for 60-70% of an editorial deck, then manually override the 2-3 flagship slides (cover, hero stat, closing) with explicit Tier 1 + 2 choreography.

### E. Animated stickers / elements

Canva's Elements library has pre-animated assets: pulsing dots, rotating gears, flowing arrows, loading spinners, animated underlines.

**Use for:**
- One accent per deck (live pulse on a "real-time" KPI, rotating arrow on a "cycle" slide)
- Replacing static icons in diagrams/flows for subtle continuous motion

**Search:** Elements panel → filter "Animated". Prefer monochrome animated elements that can be recolored to brand palette.

---

## Per-visual-style Tier 2 guidance

| Preset | Motion Path | Typewriter | Keyframe counter | Magic Animate | Animated sticker |
|---|---|---|---|---|---|
| **Minimalista** | On flows/processes only (1 slide max) | On thesis/hero slide (1 max) | On hero numbers (always if deck has them) | ❌ conflicts with restraint | Monochrome only, 1 per deck |
| **Colorido/vibrante** | On any narrative slide, bold paths, fast easing | On punchlines, letter-by-letter | Multiple allowed, bouncy easing | ✅ optional baseline | Yes, encouraged (multiple) |
| **Corporativo sóbrio** | On data flows only, subtle easing | ❌ too theatrical | Only on hero KPIs, subtle pulse | ❌ never | ❌ avoid entirely |
| **Editorial** | On narrative transitions, slow cinematic paths | On pull quotes, slow pacing | Rare — prefer drift-style reveals | ✅ baseline for most slides | Sparingly, refined style only |

---

## Timing vocabulary — advanced

For Tier 2 timings, be explicit in the playbook:

| Speed | Seconds | Use |
|---|---|---|
| **Snap** | 0.2s | Micro-interactions, sticker triggers |
| **Quick** | 0.4s | Keyframe emphasis pulses |
| **Natural** | 0.7-1.0s | Motion path for short trajectories |
| **Cinematic** | 1.5-2.5s | Full-slide motion path, typewriter on long text |
| **Contemplative** | 3s+ | Looping motion path, continuous breathe |

Easing: `ease-in-out` is the safe default. `ease-out` for arrivals (element decelerates into place). `ease-in` for exits. Linear only for mechanical/robotic feels (rare).
