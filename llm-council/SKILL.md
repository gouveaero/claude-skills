---
name: llm-council
description: "Use when a high-stakes decision, idea, plan, pivot, or piece of copy should be pressure-tested from multiple independent angles before committing. Triggers: 'council this', 'run the council', 'war room this', 'pressure-test this', 'stress-test this', 'debate this', 'leva pro conselho', 'guerra dos conselheiros', 'me dá várias perspectivas'. Strong triggers paired with a real tradeoff: 'should I X or Y', 'which option', 'what would you do', 'is this the right move', 'validate this', 'I can't decide', 'estou na dúvida entre'. Do NOT use for simple yes/no questions, factual lookups, creation or processing tasks, or a casual 'should I' with no real stakes. To critique an Instagram content script specifically, use roteiro-council instead."
metadata:
  version: 2.0.0
---

# LLM Council

## Overview

Ask one AI a question and you get one answer from one perspective — you can't tell if it's great or mid. **The council runs your question through 5 independent advisors with fundamentally different thinking lenses, has them peer-review each other anonymously, then a chairman synthesizes a final verdict.** Adapted from Andrej Karpathy's LLM Council (multiple models → anonymous peer review → chairman), run inside Claude with sub-agents instead of different models.

**Core principle:** independence first, then cross-examination. Advisors never see each other until the peer-review round, and reviews are anonymized — so verdicts come from merit, not deference.

## When to use

The council is for questions where **being wrong is expensive** and there's genuine uncertainty:
- "Should I launch a $97 workshop or a $497 course?"
- "Which of these 3 positioning angles is strongest?"
- "I'm pivoting from X to Y — am I crazy?"
- "Here's my landing page copy / pricing / hire-vs-automate call — pressure-test it."

## When NOT to use

- One right answer / factual lookup ("what's the capital of France") → just answer.
- Creation task ("write me a tweet") or processing task ("summarize this") → not a judgment call.
- Trivial "should I" with no real stakes ("should I use markdown") → just answer.
- Critiquing an **Instagram content script** (reel/carousel/caption) → use **roteiro-council** (a content-specialized fork of this skill).

## The five advisors

Thinking styles, not job titles — chosen to create three natural tensions.

| Advisor | Lens | Hunts for |
|---|---|---|
| **The Contrarian** | downside | the fatal flaw, what's missing, what will fail |
| **The First Principles Thinker** | reframe | "are we even solving the right problem?" — strips assumptions |
| **The Expansionist** | upside | overlooked opportunity, what if this works *bigger* |
| **The Outsider** | fresh eyes | zero context; catches curse-of-knowledge blind spots |
| **The Executor** | feasibility | "OK but what do you do Monday morning?" |

**The tensions:** Contrarian vs Expansionist (downside/upside), First Principles vs Executor (rethink/just-do-it), Outsider in the middle keeping everyone honest.

## Workflow

The exact sub-agent prompt templates for each step live in [references/prompts.md](references/prompts.md) — use them verbatim.

1. **Frame the question (with context).** Before framing, scan the workspace ~30s for the 2-3 files that would ground the advisors: `CLAUDE.md`, any `memory/` folder, referenced/attached files, recent council transcripts, and topic-specific data (e.g. revenue/launch results if the question is about pricing). Then reframe the user's raw question into one neutral prompt all advisors receive, including: the core decision, key context from the message, key context from workspace files, and what's at stake. Don't inject your opinion. If it's too vague ("council this: my business"), ask **one** clarifying question, then proceed.
2. **Convene (5 sub-agents in parallel).** Spawn all 5 advisors simultaneously, each with its lens + the framed question + the instruction to lean fully into its angle (no hedging, no balance). 150-300 words each. Parallel matters — sequential spawning lets earlier answers bleed into later ones.
3. **Peer review (5 sub-agents in parallel).** Anonymize the 5 responses as A-E (randomize the letter mapping). Each advisor reviews all 5 and answers: (1) strongest response + why, (2) biggest blind spot + what's missing, (3) what ALL five missed. This round is what makes the council more than "ask 5 times."
4. **Chairman synthesis.** One agent gets the question + all 5 responses (now de-anonymized) + all 5 reviews, and produces the verdict in the exact structure below.
5. **Present the verdict in chat** as scannable markdown. **Do NOT generate an HTML file or any report file** — the user reads it in the conversation.
6. **Save the transcript only if** the user asks or the question is significant enough to revisit. If saving, write `council-transcript-<topic>.md` in the project's working directory (avoid `Date.now()`-style timestamps; use a topic slug).

## The verdict structure (chairman output)

```
## Council Verdict: {short topic}

### Where the Council Agrees
{points multiple advisors converged on independently — high-confidence signals}

### Where the Council Clashes
{genuine disagreements — present both sides, explain why reasonable advisors differ; don't smooth over}

### Blind Spots the Council Caught
{what only emerged in peer review — things individuals missed that others flagged}

### The Recommendation
{a clear, direct answer with reasoning — not "it depends"; the chairman may side with a strong dissenter over the majority}

### The One Thing to Do First
{a single concrete next step — not a list}
```

## Common mistakes

| Mistake | Why it fails |
|---|---|
| Spawning advisors sequentially | Earlier responses bleed into later ones — independence is the whole point |
| Skipping anonymization in peer review | Reviewers defer to favored thinking styles instead of judging on merit |
| Chairman defaults to the majority | If the lone dissenter's reasoning is strongest, side with it and explain why |
| Counciling a trivial question | One right answer needs an answer, not five perspectives |
| Hedged verdict ("consider both sides") | The council exists to give clarity a single perspective couldn't — commit |
| Generating an HTML/report file | Step 5 is chat-only; don't produce files unless the user asks for a transcript |

## Example (condensed)

**Q:** "Council this: a $297 Claude Code course for non-technical solopreneurs — right move?"
- **Contrarian:** market flooded; $297 competes with free YouTube; non-technical = high support/refund risk.
- **First Principles:** what's the goal — revenue, authority, or a customer base? A course may be the slowest path to each.
- **Expansionist:** beginner solopreneurs are underserved; nail the entry point and $297 might be *low*.
- **Outsider:** "Claude Code" means nothing to this buyer — sell the outcome, not the tool.
- **Executor:** validate with a $97 live workshop to 50 people before building 4-8 weeks of course.

**Chairman:** agree the beginner angle has demand but the tool-specific framing won't land; clash on price (resolves on bundled support/community); the Outsider's naming point is the key blind spot. **Recommendation:** don't build yet — validate with a lower-commitment offer and reframe to the outcome. **First step:** run a $97 workshop "automate your first business task with AI" to 50 people; don't say "Claude Code" in the title.
