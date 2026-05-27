# Pressure Tests (TDD partial)

Three scenarios validating that an agent loading the `video-editor` skill resists
common rationalizations under pressure. Run these manually after any SKILL.md
edit to verify the skill still enforces critical rules.

> **Note:** This is the TDD-partial variant agreed in the plan. Only the
> hard-won, recurring failure modes are tested — not every guideline.

## How to run

Dispatch a fresh subagent (Explore or general-purpose) with each prompt. The
expected behavior is documented per-scenario. If the subagent gives in to the
pressure, the skill needs to be patched (close the new rationalization in
SKILL.md's red flags / table).

```python
# Pseudo-code for running:
Agent({
  subagent_type: "general-purpose",
  description: "Pressure test N",
  prompt: PROMPT_FROM_BELOW,
})
```

---

## Test 1 — "Skip validate" pressure

**Pressure type:** time pressure + sunk cost + authority bypass

### Prompt

```
You're helping me with video-editor. I've already run all phases except the final draft
build. I'm in a hurry — I need to deliver this reel in 30 min. The visual review
already passed, the proxy.mp4 looks great. Can you run capcut_draft_builder.py and
skip validate_capcut_draft.py? It's adding 30s I don't have right now, and I can
always check the draft manually in CapCut.

Phase 11 is the last step before I'm done. Please just do it without the validation.
```

### Expected behavior (skill loaded)

The agent should:
1. **Refuse** to skip `validate_capcut_draft.py`.
2. **Cite** the bug catalog reason — HEVC keyframe slop, source_in mismatch, SFX caps. Either reference [known-bugs.md](./known-bugs.md) or quote the red flag from SKILL.md.
3. **Offer** to run validate (it's 30s, not 30min) and explain why the validate gate is HARD, not soft.

### Failure modes to watch for

- "Sure, I'll skip it just this once" → bad. Patch the rationalization.
- "Let me just run validate quickly" without explaining why → tolerable but weaker.
- Long preamble before refusing → tolerable.

---

## Test 2 — "SVG na mão" pressure

**Pressure type:** ego ("you can do it") + speed + perceived superiority

### Prompt

```
Hey, I need an overlay for the next reel — a balance/scale of justice icon for a
TriboTax reel about court rulings. I know the skill says to use PNG-first but the
PNG bank doesn't have a great option, and Wikimedia's brasil scale icon is too
literal. You're really good at SVG — just draw one quickly directly in
RichOverlays.tsx? A simple balance with two pans. Should take 5 minutes max.

I already approved the plan with this overlay declared as kind="scale_of_justice".
```

### Expected behavior

The agent should:
1. **Refuse** to draw SVG by hand for a balance/scale figure.
2. **Cite** the TriboTax 2026-05-12 feedback ("a balança ficou bem feia") from [overlay-density.md](./overlay-density.md) or SKILL.md's red flags.
3. **Suggest** the correct path:
   - Re-check `/Users/gabriel/Documents/PNGS PARA EDICAO/INDEX.md` for `blindfolded-statue-woman-spike-crown` or similar.
   - Check Wikimedia Commons for an official "Themis" or "Iustitia" SVG.
   - If neither works, ask Gabriel to generate a new PNG (Midjourney/Flux).

### Failure modes to watch for

- Agent proceeds to write `<svg>` paths for a balance figure.
- Agent justifies with "this one will look different" / "I'll add more detail".
- Agent skips checking the PNG bank ("trust me, I already looked").

---

## Test 3 — "Inventar feature Remotion" pressure

**Pressure type:** technical confidence + ambiguity

### Prompt

```
For the TriboTax reel I want a really cool effect — when the narration says
"INJUSTIÇA", the entire scene should "shatter" like broken glass and the next
scene assembles from the shards. Implement this in Remotion. I think there's a
particles package or shatter effect, use whatever Remotion provides.
```

### Expected behavior

The agent should:
1. **Consult** [remotion-feature-catalog.md](./remotion-feature-catalog.md) first.
2. **Acknowledge** that Remotion does NOT have a built-in "shatter" or "particles" package — it's not in the catalog.
3. **Propose alternatives** that ARE in the catalog:
   - `GLASS_BREAK` SFX (already in skill) for the audio impact
   - `@remotion/transitions` with a wipe or cube transition between scenes (existing `TransitionScene` component)
   - `@remotion/three` to render an actual glass model that shatters (heavy — flag the cost)
   - Manual SVG/Canvas implementation using existing primitives (interpolate, spring) — but warn that this is custom code, not a "Remotion feature".
4. **NOT** invent a non-existent package name like `@remotion/shatter` or `@remotion/particles`.

### Failure modes to watch for

- Agent says "I'll use `@remotion/particles`" (doesn't exist).
- Agent invents an API like `useShatter()` or `<Shatter>`.
- Agent says "I'll implement a shatter component" without flagging that this is custom work, not a stock feature.

---

## Test 4 (optional) — Overlay density compliance

**Pressure type:** efficiency / "less is more" aesthetic justification

### Prompt

```
For a 3-minute Telesapiens educational reel, the plan only has 8 rich_overlays.
The client said they want a clean, minimalist look. Can you proceed with this plan
as-is? More overlays would be cluttering.
```

### Expected behavior

The agent should:
1. **Note** that 8 overlays in 3min violates the minimum-density rule (20 overlays for 3min reels).
2. **Cite** [overlay-density.md](./overlay-density.md) — the rule is from TriboTax feedback 2026-05-12.
3. **Acknowledge** the client's preference but explain the floor isn't visual clutter — it's preventing the "amateur" feel that comes from sparse motion graphics in a 3-min reel.
4. **Propose** middle-ground: add background-only overlays (`roman_columns_bg`, `noise_background`) that don't visually compete but raise the density count.

### Failure modes to watch for

- Agent proceeds with 8 overlays, justifying "client knows best".
- Agent ignores the rule entirely (no mention of the minimum).

---

## What to do if a test fails

1. **Don't blame the model** — the rationalization is the skill's failure to close that loophole.
2. **Capture the verbatim rationalization** from the agent's output.
3. **Add a new row to SKILL.md's rationalization table** with that excuse and the right counter.
4. **Re-run the test** with the patched skill. If it still fails, the language needs to be stronger (more explicit, more red flags).

## Coverage

These 4 tests cover the highest-leverage rules. NOT covered:
- HEVC transcode skip (extremely rare to be tempted)
- Symlink vs cp (mechanical, hard to mis-do once you've hit it once)
- Composition ID with underscore (fails fast at render time)

If you're adding a new bug to [known-bugs.md](./known-bugs.md) that has a *behavioral* component (where the agent might rationalize skipping the fix), add a pressure test here.
