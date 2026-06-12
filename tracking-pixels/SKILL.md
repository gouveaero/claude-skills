---
name: tracking-pixels
description: Use when the user wants to install ad pixels and Conversions APIs natively (without GTM) — Meta Pixel + CAPI, Google Ads + Enhanced Conversions, GA4 + Measurement Protocol, TikTok Pixel + Events API — or to review tracking coverage of a new/modified page. Triggers: "instalar pixel da Meta", "ativar CAPI no site", "Enhanced Conversions Google Ads", "tracking nativo sem GTM", "configurar pixel TikTok", "Conversions API", "Measurement Protocol GA4", "rastreamento de leads no site", "dedup pixel servidor", "migrar de GTM pra código nativo", "auditoria de tags no site", "install tracking on this site", "revisar tracking da página", "review page tracking", "essa página nova tá trackeada?", whenever a new client website needs tracking infrastructure, or right after a new page is created on an Exos client site. Stacks: Next.js App Router and Vite+React SPA. Reads per-client config from `<ClientFolder>/.tracking.json`. Sales events (Purchase/AddPaymentInfo) are opt-in — they fire on checkout platforms, not the site.
---

# tracking-pixels

A skill that installs **native, code-first** ad tracking infrastructure on a website. No GTM, no sGTM, no Stape — every artifact lives in the client's repo and ships with their normal CI/CD (Coolify in the Exos / Gouvêa Growth setup).

The skill covers four platforms in lockstep:

| Platform     | Client-side                | Server-side                                | Identity key |
|--------------|----------------------------|--------------------------------------------|--------------|
| **Meta**     | `fbq` (Pixel)              | Graph API `/{pixel}/events` (CAPI)         | `event_id`   |
| **Google Ads** | `gtag('event','conversion')` | Conversions API (offline / Enhanced for Leads) | `gclid + user_data` |
| **GA4**      | `gtag('event', ...)`       | Measurement Protocol `/mp/collect`         | `client_id`  |
| **TikTok**   | `ttq.track`                | Events API 2.0 `/event/track/`             | `event_id`   |

Everything is wired so the same `track('Lead', {...})` call on the client fires the Pixel AND triggers a server fan-out — deduplicated by a single `event_id` per call.

---

## What this skill does (and what it doesn't)

**Does:**
- Generates `lib/track.ts` (universal event layer), `lib/hash.ts` (SHA-256 + normalization), `lib/cookies.ts` (capture `_fbp`/`_fbc`/`_ttp`/`_ttclid`/`_ga`/`_gcl_aw`), `components/PixelBootstrap.tsx`, and the server-side fan-out endpoint.
- Reads per-client config from `<ClientFolder>/.tracking.json` and per-client secrets from `.env.local` / Coolify env vars.
- Operates in **7 modes**: install, add-event, add-platform, audit, gtm-migration, enable-lgpd, review-page. See [Mode router](#mode-router).
- Confirms every code change with the user before committing.

**Does NOT:**
- Generate GTM templates, sGTM container configs, or Stape relay setups. The whole point is to live in the project's code.
- **Install sales/checkout conversion events (`Purchase`, `AddPaymentInfo`) by default.** These fire on the checkout platform (Hotmart/Eduzz/Kiwify), not the site — installing them site-side double-counts ROAS and breaks dedup (checkout-side events carry different event_ids). Only add them when the user **explicitly requests** AND confirms the site itself processes the sale (`generate_event.py` enforces this via `--allow-sales-event`). `InitiateCheckout` (the buy-button click, which happens on the site) stays default.
- Touch live ad accounts. Conversion configuration in Meta Events Manager / Google Ads / TikTok Events Manager is a human step (the skill produces a checklist).
- Ship a default consent banner. LGPD/GDPR gates are opt-in via the `enable-lgpd` mode.
- Operate ad campaigns — that's `meta-ads-operator`. Plan analytics strategy — that's `analytics-tracking`. This skill is the **infrastructure layer** that feeds them both.

---

## Before you start — read this

This skill works with PII (emails, phones) and platform secrets (CAPI tokens, GA4 API secrets, TikTok access tokens). Three rules are non-negotiable, and you should explain them to the user up front if they haven't done a native install before:

1. **Secrets never get committed.** They live in `.env.local` (gitignored) and in the deploy platform's env-var UI (Coolify → Environment Variables). The `.tracking.json` file only carries the **name** of the env var (e.g. `"capi_token_env": "META_CAPI_TOKEN"`), never the value.
2. **PII is hashed server-side, never client-side.** The browser sends raw email/phone to your own `/api/track` endpoint (1st-party, HTTPS) and the server does SHA-256 before forwarding to Meta/Google/TikTok. Don't be tempted to "hash in the browser to be safe" — Meta needs the same hash to match users, and double-hashing breaks matching.
3. **`event_id` is the deduplication key.** The exact same UUID must appear in the Pixel call (`fbq('track', 'Lead', {...}, {eventID: '<uuid>'})`) and in the CAPI payload (`data[].event_id`). Without this, Meta will count the same lead twice. Same applies to TikTok. GA4 uses `transaction_id` for the same role on `purchase`-class events.

---

## Mode router

When the skill triggers, identify which mode the user wants. If it's ambiguous, **ask** via `AskUserQuestion` — don't guess. The 7 modes:

| Mode | When to use | Entry point |
|------|-------------|-------------|
| **install** | First-time install on a project with no native tracking | [Install workflow](#install-workflow) |
| **add-event** | A new event (e.g. `Schedule`, `Search`) needs to fire on an existing install. Sales events require `--allow-sales-event` (see "Does NOT") | `scripts/generate_event.py` |
| **add-platform** | Client already has Meta + GA4; now wants TikTok added 3 months later | [Add-platform workflow](#add-platform-workflow) |
| **audit** | Site already has GTM or other tracking — figure out what's running before changing anything | `scripts/audit_existing_tags.py` + [`references/universal-event-layer.md`](references/universal-event-layer.md) |
| **gtm-migration** | Site has live GTM and we want to switch to native without losing data | [GTM migration workflow](#gtm-migration-workflow) |
| **enable-lgpd** | Client needs LGPD/GDPR consent gating retroactively | [`references/lgpd-consent.md`](references/lgpd-consent.md) + `assets/lgpd-consent-banner.tsx` |
| **review-page** | One or more newly created/modified page files need tracking-coverage verification (auto-triggered by the Exos page hook, or manual "revisar tracking da página") | [Review-page workflow](#review-page-workflow) |

Default if the user just says "install tracking for X" → **install**.

---

## Per-client config: `.tracking.json`

Every client project has a `.tracking.json` at its root (sibling to `.meta-ads.json`, `.sendflow.json` if they exist). The skill **always** reads this first; if it doesn't exist, it generates a skeleton from `assets/tracking-config.template.json` and walks the user through filling it in.

Minimum required fields:

```json
{
  "client_code": "LL",
  "site_path": "Leticia_Lang/site",
  "stack": "vite-react-spa",
  "deploy": { "platform": "coolify", "primary_domain": "leticialang.exosmkt.com" },
  "platforms": {
    "meta": { "enabled": true, "pixel_id": "...", "capi_token_env": "META_CAPI_TOKEN" }
  }
}
```

Full schema in [`assets/tracking-config.template.json`](assets/tracking-config.template.json). Each platform has an `enabled` boolean — the fan-out endpoint short-circuits when a platform is disabled, so it's safe to ship with only one platform turned on.

---

## Stack detection

Run `scripts/detect_stack.sh <site_path>` to identify the framework. It looks at `package.json` (`next` → nextjs-app-router; `vite` + `react` → vite-react-spa). If detection is ambiguous (e.g. a Vite + React Router app that pretends to be Next-like), ask the user — don't guess.

Supported stacks in V1:
- **`nextjs-app-router`** → template at [`assets/nextjs-app-router/`](assets/nextjs-app-router/). The `app/api/track/route.ts` route handler IS the fan-out endpoint.
- **`vite-react-spa`** → template at [`assets/vite-react-spa/`](assets/vite-react-spa/). Because Vite has no server runtime, this template adds a **sidecar Node/Bun service** (`tracking-sidecar/`) deployed as a separate Coolify app at `track.<domain>` exposing `/api/track`.

Out of scope: HTML estático, Astro, Nuxt, SvelteKit, mobile. Adding a stack later is an additive change (new `assets/<stack>/` folder) — don't refactor the skill to support hypothetical stacks now.

---

## Install workflow

The default mode. Six steps:

1. **Confirm scope.** Read `.tracking.json` (or generate skeleton). Confirm which platforms are `enabled: true` and which events are listed in `events[]`. If the user said "install Meta and GA4" but `.tracking.json` has TikTok enabled, surface the mismatch and ask. If `events[]` or the user request includes `Purchase`/`AddPaymentInfo`, **stop and apply the sales-event rule** (see "Does NOT" above): warn that purchases fire on the checkout platform and require explicit confirmation before including them.

2. **Detect the stack.** Run `scripts/detect_stack.sh`. Set `stack` in `.tracking.json` if missing.

3. **Copy template files** from `assets/<stack>/` into the site. The skill copies, never symlinks — the generated code becomes part of the client's repo.

4. **Wire up the entry point**:
   - Next.js App Router: import `<PixelBootstrap />` in `app/layout.tsx`, just above `{children}`.
   - Vite SPA: import `<PixelBootstrap />` in `src/main.tsx` (or the equivalent root component).

5. **Generate `.env.example`** with placeholders for every env var referenced by enabled platforms. The user fills `.env.local` (gitignored) and the Coolify env-var UI. See [`references/coolify-env-setup.md`](references/coolify-env-setup.md) for the Coolify naming convention.

6. **Show diff, run checklist.** Print `git diff`, then [`assets/post-install-checklist.md`](assets/post-install-checklist.md). Wait for explicit user approval before any `git add` / `git commit`.

Heads-up the user about the **Coolify env-var step** specifically. The site will deploy without secrets and silently fail to fire CAPI events. Don't let this happen — the checklist makes it explicit.

---

## Add-platform workflow

Client comes back 3 months after install asking to add TikTok. The skill needs to:

1. Read `.tracking.json`. Flip the platform's `enabled: false` → `true` and fill in `pixel_id` / `access_token_env`.
2. Append the env var to `.env.example`.
3. Add the platform's `init` block to `components/PixelBootstrap.tsx` (read the existing file with `Read`, find the consent-gate / init block, append the new platform's init alongside existing ones — don't replace).
4. Confirm the fan-out endpoint already imports a `sendTo<Platform>` function (it does in our templates — they're all generated upfront, just gated by `enabled`). If the user has been editing the endpoint, do a more careful merge.
5. Run the checklist for that platform only.

Same idea for adding a new standard event — `scripts/generate_event.py` exists for that.

---

## GTM migration workflow

Most legacy Exos sites have GTM and we want to switch to native without losing data. Don't rip out GTM in step 1 — run them in parallel.

1. **Audit first.** `scripts/audit_existing_tags.py <site_path>` produces a report of every `fbq` / `gtag` / `ttq` / `googletagmanager.com` reference + which standard events fire and where. **Always read this before installing.** Letícia Lang's site has GTM-T9NN3458 and the audit will surface it.
2. **Install native in parallel.** Run the standard install workflow. The Pixel will fire twice (GTM + native) but Meta will dedup by `event_id` IF we configure GTM to forward the same `event_id`. In practice, GTM Pixel doesn't know our native `event_id`, so we accept the GTM-side as "no-dedup" and rely on **comparing counts** between the two paths to validate parity.
3. **Run paridade window** (7–14 days). User opens Meta Events Manager → Diagnostics → checks that CAPI event count is within ±5% of Pixel event count. If yes → step 4. If not → debug (cookie capture? consent gate? endpoint 500?).
4. **Disable GTM tags** (user removes `gtm.js` from the site `<head>` and pauses the GTM container — manual step, **the skill does not touch GTM Workspace**).
5. **Final smoke test.** Re-run the audit, confirm GTM strings are gone.

---

## Review-page workflow

Input: one or more page file paths (e.g. `src/pages/NovaLanding.tsx`, `app/promo/page.tsx`). Triggered automatically by the Exos page hook (PostToolUse on Write) or manually ("revisa o tracking dessa página").

0. **Check install state.** Locate `<ClientFolder>/.tracking.json` and the universal layer (`lib/track.ts` / `src/lib/track.ts`). If the project has **no native tracking** (e.g. a GTM-only or iframe-form site), do NOT fail: report "no native tracking installed" and suggest running **install** mode (or audit → gtm-migration if GTM is live). Stop there.
1. **PageView coverage.** `PixelBootstrap` fires `PageView` on hard load and on client-side route changes (the templates listen for pathname changes). If the site's bootstrap predates that fix or was edited, check whether the page is reachable only via client navigation and flag missing route-change coverage.
2. **CTA/form coverage.** Every CTA button, form submit, scheduling link, and WhatsApp/phone link on the page must have an appropriate `track()` call: `Lead` (capture forms), `Contact` (WhatsApp/phone), `Schedule` (booking), `InitiateCheckout` (buy buttons), `ViewContent`/`Search` where relevant. **Never propose `Purchase`/`AddPaymentInfo`** — sales events are opt-in (scope rule above).
3. **Param correctness.** `value`/`currency` on checkout-class events; email/phone passed **raw** to `track()` on form submits (the server hashes); no PII hashed client-side; `externalId` passed when the form/CRM returns a stable ID.
4. **Config parity.** Every event used on the page is listed in `.tracking.json` `events[]` — wire missing ones via `scripts/generate_event.py`.
5. **Output.** A short coverage report (table: element → expected event → status) + proposed diffs. Apply diffs **only with explicit user approval**. Pages with genuinely no conversion surface (privacy policy, thank-you-only) pass with a "PageView-only" verdict — that is not a failure.

---

## Critical heads-up (things that bite people)

- **Graph API version.** Lives in `.env` as `META_GRAPH_VERSION` (default `v25.0` as of Feb 2026). **Do not hardcode** in generated TS. Meta drops versions after ~2 years — see [`references/meta-capi.md`](references/meta-capi.md) for the changelog link.
- **GA4 cookie format changed in May 2025.** The old regex on `_ga` (`GA1.2.X.Y` → `X.Y`) broke. The skill's templates use `gtag('get', '<measurement_id>', 'client_id', cb)` instead. See [`references/ga4-mp.md`](references/ga4-mp.md).
- **`_fbc` is conditional.** The cookie only exists if the user landed via `?fbclid=...`. Never synthesize one from nothing. The template's `cookies.ts` does the right thing — if the user edits it, remind them.
- **`event_id` dedup window is 48h.** If your CAPI POST is delayed (queue backlog, retry loop), Meta may have already accepted the Pixel-side event and forget about it. Don't add long retry delays in the fan-out endpoint.
- **GA4 reserved event names.** Some names (`session_start`, `first_visit`, `app_install`, etc.) cannot be used — GA4 silently drops them. List in [`references/ga4-mp.md`](references/ga4-mp.md).
- **PII consent.** Default mode is "no consent gating, send everything". This is acceptable in Brazil for most B2C / professional services contexts where the user already opted in by submitting a form. If the user wants strict LGPD compliance (consent banner before any pixel fires) → switch to `enable-lgpd` mode. The skill is **capable** of LGPD compliance but does not enforce it.

---

## Coolify integration notes

- The Exos VPS (`coolify.exosmkt.com`, `187.127.30.29`) and Gabriel's personal VPS (Gouvêa Growth, `187.127.2.180`) are **separate**. Never put Exos client secrets on the personal VPS or vice versa.
- The `vite-react-spa` template's `tracking-sidecar/` is deployed as a **separate Coolify app** with a separate `Dockerfile`. Recommended naming: `<client_code>-tracking` (e.g. `leticialang-tracking`), routed at `track.<domain>`.
- Env vars go in Coolify UI → app → Environment Variables. The skill's checklist will print the exact list of vars to copy.
- See [`references/coolify-env-setup.md`](references/coolify-env-setup.md) for the full how-to including the Coolify API approach (faster than clicking through UI for many vars).

---

## Files in this skill

Read the references only when you actually need them — they're not part of every invocation.

- [`references/meta-capi.md`](references/meta-capi.md) — Graph API endpoint, payload, hashing rules, dedup
- [`references/google-ads.md`](references/google-ads.md) — Enhanced Conversions Web + Leads
- [`references/ga4-mp.md`](references/ga4-mp.md) — Measurement Protocol, reserved names, DebugView
- [`references/tiktok-events-api.md`](references/tiktok-events-api.md) — Events API 2.0 schema
- [`references/universal-event-layer.md`](references/universal-event-layer.md) — `track()` contract, name translation table
- [`references/cookies-and-attribution.md`](references/cookies-and-attribution.md) — `_fbp` / `_fbc` / `_ttp` / `_ttclid` / `_ga` / `_gcl_aw`
- [`references/lgpd-consent.md`](references/lgpd-consent.md) — Opt-in consent gating
- [`references/coolify-env-setup.md`](references/coolify-env-setup.md) — Per-VPS env-var workflow

- [`assets/nextjs-app-router/`](assets/nextjs-app-router/) — Template for Next.js sites
- [`assets/vite-react-spa/`](assets/vite-react-spa/) — Template for Vite SPAs (includes sidecar)
- [`assets/tracking-config.template.json`](assets/tracking-config.template.json) — `.tracking.json` skeleton
- [`assets/lgpd-consent-banner.tsx`](assets/lgpd-consent-banner.tsx) — Opt-in banner for `enable-lgpd` mode
- [`assets/post-install-checklist.md`](assets/post-install-checklist.md) — Post-install QA

- [`scripts/detect_stack.sh`](scripts/detect_stack.sh) — Stack detection
- [`scripts/audit_existing_tags.py`](scripts/audit_existing_tags.py) — Find existing tracking in a repo
- [`scripts/generate_event.py`](scripts/generate_event.py) — Idempotent add-event
