---
name: roteiro-council
description: "Use when the user wants a critique, pressure-test, or red-team of an Instagram/social content SCRIPT before publishing — a reel script, carrossel/carousel, caption, single post, or story. Triggers: 'critica esse roteiro', 'esse carrossel tá bom?', 'esse hook funciona?', 'detona esse roteiro', 'red-team esse conteúdo', 'esse roteiro vai viralizar?', 'revisa esse roteiro de reel', 'me dá um parecer brutal desse post', 'pressure-test this script', 'council this reel', 'critique this caption', 'roast my carousel'. For a non-content decision use llm-council; to GENERATE content instead of critiquing it, use content-machine-pro / copywriting / reels-vhoe."
metadata:
  version: 1.0.0
---

# Roteiro Council — adversarial critique of a content script

## Overview

A content-specialized fork of **llm-council**. You convene **9 independent, adversarial advisors** to pressure-test an Instagram/social script *before it ships*, run an anonymized peer review, then a chairman returns a **scored verdict + one concrete rewrite of the weakest element.** This skill **critiques; it does not generate** — full rewrites route to a generator (see Cross-references).

**Core principle:** a pre-publish script fails for one of six craft reasons — the hook doesn't earn the next second, the body leaks attention, the language is harder than it needs to be, it reads like AI slop, it doesn't sound like the brand, or it gives the viewer no psychological reason to act. One advisor owns each. Three more generalist advisors judge the whole piece. They hunt for what's **wrong** — no praise. When advisors conflict, the priority ladder decides: **Accurate > Clear > Specific > Voiced > Stylish.**

## When to use

- The user has a **draft** script (reel, carousel, caption, post, story) and wants it judged before publishing.
- Triggers: "critica esse roteiro", "esse hook funciona?", "esse carrossel tá bom?", "detona/red-team esse conteúdo", "pressure-test this", "council this reel", "roast my carousel".

## When NOT to use

- Non-content decision or general question → **llm-council**.
- User wants to GENERATE, not critique → carousel: **content-machine-pro** (or **content-machine**, **content-machine-saif**, **carrossel-vhoe-editorial**, **carrossel-vhoe-conceito**); reel: **reels-vhoe** / **social-content** / **content-repurposer**; caption: **copywriting** (from scratch) / **copy-editing** (improve existing); ad: **ad-creative**.
- "Right craft, wrong pillar/format" is a strategy problem → **content-strategy**.

## The panel (9 advisors — each a parallel sub-agent, 150-300 words, adversarial)

Full sub-agent templates with their reference banks: [references/advisor-templates.md](references/advisor-templates.md). Proof every content principle is owned (nothing omitted): [references/coverage-map.md](references/coverage-map.md).

**Craft specialists (own a principle):**

| # | Advisor | Owns / hunts |
|---|---|---|
| A1 | **Hook Assassin** | `viral-hooks`: 4 Hook Killers (DELAY/CONFUSION/IRRELEVANCE/DISINTEREST), platform deadline, banned openers, slide-1-as-hook, A-vs-B with a real open question |
| A2 | **Retention Auditor** | `storytelling`: The Dance (BUT/THEREFORE, ban "and then"), Direction (last dab), Story Lens, Rhythm, Tone, hook handoff; ~2 words/sec length budget; no fabricated biography |
| A3 | **Clarity Inspector** | `dumbify`: reading level (~6th grade hook / ~8th body), 7 moves, "simple language, not simple ideas" |
| A4 | **Anti-Slop Prosecutor** (final filter + tie-breaker) | `anti-ai-writing`: 5 diseases, specificity ladder (demand L3+), negative-parallelism ban, vocab/verb blocklists, the priority ladder |
| A5 | **Voice & Brand Marshal** | `voice-dna`: judge against the profile or flag **"voice unverified — no sample"**; brand non-negotiables; viewer-POV vs creator-POV; swap-the-logo test |
| A6 | **Persuasion Strategist** | `marketing-psychology`: *why would the viewer act?* — missing trigger (reciprocity, social proof, scarcity/urgency, authority, loss aversion), unhandled objection, negative framing, CTA with no psychological lever |

**Generalists (judge the whole piece — original council spirit):**

| # | Advisor | Lens |
|---|---|---|
| G1 | **The Contrarian** | the single fatal flaw — "why does this flop?"; cross-checks the specialists' findings ("which of these actually kills the post?") |
| G2 | **The Outsider** | zero-context cold scroller; catches niche jargon, unstated assumptions, curse-of-knowledge blind spots the specialists (inside the brief) miss |
| G3 | **The Expansionist** | the only opportunity lens (finds what's *missing*, not what's wrong): the bigger swing, the adjacent angle, the remix, what would make it 10× |

## Format-adaptive logic

Classify the artifact, then the hook/body/close units shift. Classify by the user's label; else infer (numbered slides ⇒ carousel; duration or "fala/spoken" ⇒ reel; single block + CTA ⇒ caption; "story/frame/sticker" ⇒ story). Ambiguous → ask **one** question.

| | Hook unit (A1) | Body unit (A2) | Close / last dab |
|---|---|---|---|
| **Reel** | first line, ~1-2s | full spoken script vs word budget (2 w/s) | last spoken line |
| **Carousel** | **slide 1, judged standalone** | slide-by-slide; no "and then" between slides; mid-deck dip | **last slide = CTA / last dab** |
| **Caption/post** | first line above the "…mais" fold | caption arc, one idea | last line + CTA |
| **Story** | first frame, ~1s | 1-3 frame micro-arc | final-frame CTA |

## Workflow (6 steps, from llm-council)

1. **Frame.** Read available context BEFORE convening: project `CLAUDE.md`, the brand-law doc + personas, and any `voice-dna` profile. **Discover project-local content skills** (e.g. Vhoe `carrossel-vhoe-editorial` / `reels-vhoe`) and pull their banks *conditionally* when present. Classify the format. Extract hook/body/close units, platform, duration/slide count, brand non-negotiables, voice profile (or mark "voice unverified"). No script, or a non-content decision → route to **llm-council**. Vague request → optionally sharpen with **enhance-prompt** first.
2. **Convene** A1-A6 + G1-G3 as **9 independent sub-agents in one parallel batch.** Each gets only its template + framed context + format flag + its reference banks. No advisor sees another's output. 150-300 words, adversarial, each ending in a severity tag (FATAL / WEAK / OK).
3. **Peer review (parallel).** Relabel the 9 outputs A-I (strip lens names). Each advisor reviews the others and answers: strongest critique, biggest blind spot any advisor missed, what ALL of them missed about *this* script.
4. **Chairman synthesis.** Reconcile via the priority ladder → the scored verdict in [references/verdict-template.md](references/verdict-template.md).
5. **Present the verdict in chat** (scannable scorecard; no raw advisor transcripts unless asked; **no HTML/report file**).
6. **Optional** — offer to save the transcript; then offer the fork: "Quer que eu reescreva o roteiro inteiro?" → if yes, hand off to the right generator. The council itself never rewrites the whole piece — only the one weakest element (see verdict).

## Verdict

A scored scorecard: **6 craft dimensions** (Hook / Retention / Clarity / Anti-slop / Voice-brand / Persuasion) each with a verdict + score + worst finding; a **"Generalist verdict"** line (Contrarian fatal flaw / Outsider blind spot / Expansionist opportunity); the single most damaging problem (with the ladder reason it ranks #1); a prioritized fix list; and **one concrete rewrite of the weakest element** (e.g. the hook in 3 ways). Template: [references/verdict-template.md](references/verdict-template.md).

## Cross-references (by name — do not @-link, do not duplicate their content)

| When | Skill | Use |
|---|---|---|
| Framing / input | `voice-dna`, `marketing-psychology` | pull the voice profile + audience-psychology lens |
| Framing (conditional, project) | `carrossel-vhoe-editorial`, `reels-vhoe` | pull brand-specific hook/scene banks when working in that project |
| Advisor enrichment | `content-machine` (56-hook bank, 28 anti-slop patterns), `ad-creative` (8 angles), `social-content` (hook types, platform/pillar voice), `copy-editing` (7 sweeps, specificity table), `copywriting` (CTA formulas), `content-repurposer` (extraction/arc) | feed the matching advisor concrete banks (see coverage-map) |
| Step 6 handoff — generate | `content-machine-pro` / `content-machine-saif` / `carrossel-vhoe-editorial` (carousel) · `reels-vhoe` / `social-content` (reel) · `copywriting` / `copy-editing` (caption) · `ad-creative` (ad) | full rewrite if the user wants generation, not critique |
| Strategy escalation | `content-strategy`, `marketing-ideas` | "right craft, wrong pillar/format/channel" |
| Pre-step | `enhance-prompt` | sharpen a vague critique request before convening |

## Common mistakes

- **Praising.** The council finds what's wrong. Strengths get one line at most.
- **Letting an advisor see another's output before peer review** — kills independence (the whole point).
- **Generating a full rewrite inside the council** — only the weakest element gets rewritten; full rewrites route out.
- **Judging voice against a generic standard when a profile exists** — or forgetting the "voice unverified" flag when none does.
- **Scoring a carousel's slide 1 as if slide 2 exists** — slide 1 must stand alone.
- **Ranking a "stylish" fix over an accuracy/clarity fix** — the ladder is law.
- **Duplicating a content-skill's rules into the verdict** — cite the owner; pull only the extra banks.

## Anti-overfitting

The nine lenses are universal; the brand law, platform deadlines, and pulled banks are the variables — re-read the project's brand/voice docs each run, don't bake one client's rules in. Don't force all nine to scream FATAL; an honest "5 OK, 1 WEAK" verdict is the goal. This is a judgment skill — advisors reason about *this* script, they don't paste rubric text.
