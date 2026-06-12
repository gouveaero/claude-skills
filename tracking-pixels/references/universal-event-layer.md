# Universal Event Layer — the `track()` contract

The whole skill rests on one client-side function: `track(name, params)`. This file documents the contract, the platform-by-platform translation, and the dedup mechanic.

## The contract

```ts
// lib/track.ts
type EventName =
  | 'PageView'
  | 'ViewContent'
  | 'Lead'
  | 'CompleteRegistration'
  | 'InitiateCheckout'
  | 'AddPaymentInfo'
  | 'Purchase'
  | 'Contact'
  | 'Schedule'
  | 'SubmitApplication'
  | 'Search'
  | 'AddToCart';

type EventParams = {
  value?: number;
  currency?: string;
  email?: string;
  phone?: string;
  firstName?: string;
  lastName?: string;
  externalId?: string;
  contentIds?: string[];
  contentType?: 'product' | 'product_group';
  contents?: Array<{ id: string; quantity?: number; price?: number; name?: string }>;
  searchString?: string;
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
  meta?: Record<string, unknown>;
};

export async function track(name: EventName, params: EventParams = {}): Promise<void>;
```

`track()` is **isomorphic** — safe to call from client components, but the client-side firing (Pixel, gtag, ttq) is guarded with `typeof window !== 'undefined'`. On the server, it can be called from route handlers, server actions, etc.

The function does three things, in order:

1. Generate `event_id = crypto.randomUUID()` and `event_time = Math.floor(Date.now() / 1000)`. These are reused across all platforms in the same call.
2. **Client-side fan-out** (only if `typeof window !== 'undefined'`): fire `fbq`, `ttq.track`, `gtag('event', ...)` with the universal name mapped per platform.
3. **Server-side fan-out**: `fetch('/api/track', ...)` with the payload. Server reads cookies (`_fbp`, `_fbc`, `_ttp`, `_ttclid`, `_ga`, `_gcl_aw`), captures IP/UA, hashes PII, and POSTs to Meta CAPI, GA4 MP, TikTok Events API in parallel.

The same `event_id` is used in step 2 (passed to `fbq` as `{eventID}`, to `ttq` as `{event_id}`, to `gtag` as `transaction_id`) AND in step 3 (passed in the body, used by the server in each fan-out call). **This is the dedup key.**

## Name mapping table

| Universal | Meta (`fbq` + CAPI `event_name`) | GA4 (`gtag`/MP `name`) | TikTok (`ttq` + CAPI `event`) |
|-----------|----------------------------------|------------------------|-------------------------------|
| `PageView` | `PageView` | `page_view` | `Browse` |
| `ViewContent` | `ViewContent` | `view_item` | `ViewContent` |
| `Lead` | `Lead` | `generate_lead` | `SubmitForm` |
| `CompleteRegistration` | `CompleteRegistration` | `sign_up` | `CompleteRegistration` |
| `InitiateCheckout` | `InitiateCheckout` | `begin_checkout` | `InitiateCheckout` |
| `AddPaymentInfo` † | `AddPaymentInfo` | `add_payment_info` | `AddPaymentInfo` |
| `Purchase` † | `Purchase` | `purchase` | `CompletePayment` |
| `Contact` | `Contact` | `contact` (custom) | `Contact` |
| `Schedule` | `Schedule` | `schedule` (custom) | `ClickButton` |
| `SubmitApplication` | `SubmitApplication` | `submit_application` (custom) | `SubmitForm` |
| `Search` | `Search` | `search` | `Search` |
| `AddToCart` | `AddToCart` | `add_to_cart` | `AddToCart` |

† **Opt-in only** — sales/checkout events stay in the `EventName` union (capability preserved) but are never installed by default: purchases fire on the checkout platform (Hotmart/Eduzz/Kiwify), not the site. See the scope rule in SKILL.md.

Implementation in `lib/track.ts` uses three lookup objects (`META_NAME`, `GA4_NAME`, `TIKTOK_NAME`) — direct map, no string mangling.

## Params translation

The universal `params` object uses camelCase. Each platform expects different field names and shapes:

| Universal | Meta `custom_data` | GA4 `params` | TikTok `properties` |
|-----------|-------------------|--------------|---------------------|
| `value` | `value` | `value` | `value` |
| `currency` | `currency` | `currency` | `currency` |
| `contentIds` | `content_ids` | (in `items[]`) | (in `contents[]`) |
| `contentType` | `content_type` | n/a | (in `contents[]`) |
| `contents` | `contents` | `items` (different shape — `item_id`, `item_name`) | `contents` |
| `searchString` | `search_string` | `search_term` | `search_string` |

`email`, `phone`, `firstName`, `lastName`, `externalId`, `city`, `state`, `postalCode`, `country` go into `user_data` (Meta), `params.user_data` (GA4), or `user` (TikTok) — handled by the server fan-out, **never sent client-side raw to the platforms.** The browser passes them raw to your `/api/track`, server hashes once.

## Dedup mechanic in detail

The 4 platforms have 3 different dedup behaviors:

| Platform | Dedup field | Window | What happens if dedup fails |
|----------|-------------|--------|------------------------------|
| Meta | `event_id` + `event_name` | 48h | Event counted twice (Pixel + CAPI) → 2× conversions in reports |
| TikTok | `event_id` | ~48h (not officially published) | Same — 2× conversions |
| GA4 | `transaction_id` (purchase events only) | 90 days | Duplicate purchase entries; non-purchase events are not deduplicated by default |
| Google Ads | `transaction_id` (conversion events) | 90 days | Counts as repeat conversion (which may be desired or not) |

**Key insight**: GA4 and Google Ads only dedup *purchases/conversions* — other event types (page_view, generate_lead) aren't deduped at all, but they also aren't reported as "conversions" so it doesn't matter for ROAS calculations. Meta and TikTok dedup *everything*.

The skill uses `event_id = randomUUID()` everywhere, also passing it as `transaction_id` to gtag (which works for both GA4 and Google Ads dedup of purchase-class events).

## What client-side and server-side each do

| Step | Client (`lib/track.ts`) | Server (`/api/track`) |
|------|-------------------------|------------------------|
| Generate `event_id` | Yes | n/a (received from client) |
| Fire Pixel `fbq('track', ...)` | Yes | n/a |
| Fire `gtag('event', ...)` | Yes | n/a |
| Fire `ttq.track(...)` | Yes | n/a |
| Read cookies (`_fbp`, etc.) | n/a | Yes (from `Cookie` header) |
| Read IP / UA | n/a | Yes (from `x-forwarded-for`, `user-agent`) |
| Hash PII | n/a | Yes (`lib/hash.ts`) |
| POST to Meta CAPI | n/a | Yes |
| POST to GA4 MP | n/a | Yes |
| POST to TikTok Events API | n/a | Yes |
| POST to Google Ads (conversion upload) | (via gtag client-side EC for Web) | n/a in default; yes for EC for Leads (offline upload) |

## Why not just fire from the server?

Client-side firing matters because:
1. Pixels capture `_fbp`/`_fbc`/`_ttp` cookies — without the client-side script, those cookies don't exist and match quality drops.
2. Browser-side `gtag` does Enhanced Measurement auto-events (scroll, outbound click, video engagement) that you'd have to reimplement.
3. Some ad platforms (notably Meta) penalize accounts that *only* send via CAPI — they want both signals.

Why not just fire from the client?

1. Ad blockers (uBlock, Brave, Pi-hole) block `connect.facebook.net`, `googletagmanager.com`, `analytics.tiktok.com` — your conversion data has a 20–40% hole. Server-side firing is invisible to client ad-blockers.
2. iOS Safari's ITP truncates 1st-party cookies set by JS to ~7 days. Server-side via HTTP-set cookies bypasses this.
3. PII can't safely live in client-side bundles or be sent to 3rd-party domains.

So you do both. The Universal Event Layer is the contract that makes "both" easy.

## Adding a new event type

Two places to edit:

1. `lib/track.ts` — add to `EventName` union + extend the 3 mapping objects.
2. `app/api/track/route.ts` (or sidecar) — if the new event needs custom server logic (e.g. fetching extra data from your DB to enrich), add a branch. Otherwise the generic fan-out handles it.

The `scripts/generate_event.py` script does this idempotently — invoke it instead of editing by hand.

## Adding a new platform

Edit four places:

1. `lib/track.ts` — add a third client-side fire (if the new platform has a Pixel snippet) and a fourth `fetch` to `/api/track` is unchanged.
2. `app/api/track/route.ts` — add `sendToNewPlatform()` function + add it to `Promise.allSettled([...])`.
3. `components/PixelBootstrap.tsx` — add the `<Script>` init for the new Pixel.
4. `.tracking.json` — add the new platform under `platforms`.

V1 only ships 4 platforms (Meta, Google Ads, GA4, TikTok). Adding LinkedIn Insight, Pinterest, Reddit, Snap is a `add-platform` operation later.
