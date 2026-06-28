---
name: voice-dna
description: Use when writing or auditing ANY content that must match a specific person's or brand's real voice — captions, scripts, posts, emails — instead of a generic voice. Also use when no voice profile exists yet and one needs to be built from ~20 real posts or video transcripts. Companion to storytelling, viral-hooks, anti-ai-writing, and roteiro-council, which read this profile to check voice.
---

# Voice-DNA

This skill holds **one person's or brand's voice profile** — how they actually sound (sentence shapes, signature phrases, hooks, CTAs, anti-voice) — so every other writing skill matches that voice instead of a generic one.

## STATUS: no profile built yet

There is no saved voice profile below this line. Until one exists, any skill that checks voice (`viral-hooks`, `storytelling`, `anti-ai-writing`, `roteiro-council`) must flag **"voice unverified — no sample to check against"** rather than pretend a voice check happened.

## How to build the profile (≈2 minutes)

The build is intentionally human-driven and lives in [README.md](README.md) in this folder. In short:
1. Gather ~20 real posts or — better — spoken transcripts of the person's own short-form videos.
2. Paste them into Claude with the copy-paste prompt in `README.md` (it extracts *how* they sound, not *what* they wrote about).
3. Claude returns a `voice-dna.md` profile.
4. **Paste that profile directly below this section** (replacing the STATUS block above with the real profile). From then on this skill fires like the others.

## Multiple voices

For more than one brand/person, keep a profile per voice. The simplest convention: one folder per voice (e.g. a project-local `.claude/skills/voice-dna-<brand>/SKILL.md`), each built with the same prompt. `roteiro-council`'s framing step looks for a relevant profile before convening its Voice & Brand Marshal.

## Re-run periodically

Voice drifts. Re-run the build prompt every few months with a fresh 20-post sample to keep the profile current.
