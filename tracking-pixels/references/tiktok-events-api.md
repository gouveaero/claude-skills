# TikTok — Events API 2.0 + Pixel

TikTok migrated to "Web Events API 2.0" in 2024. The skill targets 2.0 — the older `pixel/track` endpoint still works but is on the deprecation path. Always use the new schema.

## Endpoint

```
POST https://business-api.tiktok.com/open_api/v1.3/event/track/
Access-Token: {LONG_LIVED_TOKEN}
Content-Type: application/json
```

Note the **trailing slash** on `/event/track/` — TikTok's gateway will reject without it.

- `Access-Token` is generated in TikTok Events Manager → Settings → Generate Access Token. It's long-lived (no refresh flow needed). Lives in env var `TIKTOK_ACCESS_TOKEN`.
- Pixel ID lives in `.tracking.json` as `platforms.tiktok.pixel_id`.

Spec: https://business-api.tiktok.com/portal/docs?id=1771101303285761
Postman canonical: https://www.postman.com/tiktok/tiktok-api-for-business/request/n62cjo9/pixel-events-track-prod

## Body shape

```json
{
  "event_source": "web",
  "event_source_id": "<PIXEL_ID>",
  "partner_name": "tracking-pixels-skill-v1",
  "test_event_code": "TEST12345",
  "data": [
    {
      "event": "CompletePayment",
      "event_time": 1717000000,
      "event_id": "<uuid>",
      "user": {
        "ttclid": "<from ?ttclid query or _ttclid cookie>",
        "ttp": "<from _ttp cookie>",
        "external_id": "<sha256 hex of your user_id>",
        "email": "<sha256 hex>",
        "phone": "<sha256 hex of E.164 without +>",
        "first_name": "<sha256 hex>",
        "last_name": "<sha256 hex>",
        "city": "<sha256 hex>",
        "state": "<sha256 hex>",
        "zip_code": "<sha256 hex>",
        "country": "<sha256 hex>",
        "ip": "1.2.3.4",
        "user_agent": "Mozilla/..."
      },
      "page": {
        "url": "https://...",
        "referrer": "https://..."
      },
      "properties": {
        "currency": "BRL",
        "value": 149.99,
        "contents": [
          { "content_id": "SKU-1", "content_type": "product", "content_name": "Course X", "quantity": 1, "price": 149.99 }
        ]
      }
    }
  ]
}
```

## Standard events (use these names — case-sensitive)

`ViewContent`, `ClickButton`, `Search`, `AddToWishlist`, `AddToCart`, `InitiateCheckout`, `AddPaymentInfo`, `CompletePayment`, `PlaceAnOrder`, `Contact`, `Download`, `SubmitForm`, `CompleteRegistration`, `Subscribe`.

Note TikTok uses `CompletePayment` where Meta uses `Purchase`, and `SubmitForm` where Meta uses `Lead`. The skill's `lib/track.ts` maps between them automatically (see [`universal-event-layer.md`](universal-event-layer.md)).

## Hashing rules (SHA-256, hex, lowercase)

Hash these:
- `email` — lowercase + trim, then SHA-256
- `phone` — E.164 **without `+`** (e.g. `5511999999999`), then SHA-256
- `external_id` — your raw user ID, then SHA-256
- `first_name`, `last_name`, `city`, `state`, `zip_code`, `country` — lowercase + trim, then SHA-256

Don't hash:
- `ttclid`, `ttp` — raw cookie values
- `ip` — raw
- `user_agent` — raw

The skill's `lib/hash.ts` uses TikTok's no-`+` phone convention (different from Google's E.164-with-`+`). The phone normalizer takes a config flag.

## `ttclid` and `_ttp` cookies

- **`ttclid`** — TikTok's click ID, comes in as `?ttclid=...` on landing from a TikTok ad. Capture client-side on first arrival, persist as `_ttclid` cookie (1st-party, 90 days). The Pixel script does **not** set this automatically — you have to do it (the skill's `lib/cookies.ts` handles it).
- **`_ttp`** — set automatically by the TikTok Pixel script when it loads. Browser-fingerprint-ish identifier, 1st-party, 13 months. The server just reads and forwards.

Forward both to `user.ttclid` and `user.ttp` in the CAPI payload — they're TikTok's strongest matching signals.

## Dedup with `event_id`

Same model as Meta: TikTok dedups events when the same `event_id` arrives from Pixel and Events API. Window is similar to Meta's (TikTok doesn't publish the exact length, but treat 48h as safe).

The client-side `ttq.track` call needs `event_id` passed in the options:

```ts
window.ttq?.track('CompletePayment', { value: 149.99, currency: 'BRL' }, { event_id: '<uuid>' });
```

The server-side payload has `event_id` in each `data[]` entry. Match them exactly.

## Pixel install (client-side)

In `components/PixelBootstrap.tsx`:

```tsx
<Script id="tiktok-pixel" strategy="afterInteractive">{`
  !function (w, d, t) {
    w.TiktokAnalyticsObject=t;
    var ttq=w[t]=w[t]||[];
    ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie"];
    ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};
    for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);
    ttq.instance=function(t){for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e};
    ttq.load=function(e,n){var i="https://analytics.tiktok.com/i18n/pixel/events.js";ttq._i=ttq._i||{};ttq._i[e]=[];ttq._i[e]._u=i;ttq._t=ttq._t||{};ttq._t[e]=+new Date;ttq._o=ttq._o||{};ttq._o[e]=n||{};var o=document.createElement("script");o.type="text/javascript";o.async=!0;o.src=i+"?sdkid="+e+"&lib="+t;var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(o,a)};
    ttq.load('${process.env.NEXT_PUBLIC_TIKTOK_PIXEL_ID}');
    ttq.page();
  }(window, document, 'ttq');
`}</Script>
```

`ttq.page()` fires `Browse` event on load.

## Test events

1. Events Manager → your Pixel → Test Event tab → copy code (e.g. `TEST12345`).
2. Set `TIKTOK_TEST_EVENT_CODE=TEST12345`, include in body root as `test_event_code`.
3. Fire events from dev → appear in Test Event tab within ~30 seconds.
4. **Remove from production** — `test_event_code` makes events invisible in real reports.

## Match quality dashboard

TikTok Events Manager → Diagnostics → "Event Matching Score" shows quality 0–100 based on:
- Presence of `email`, `phone`, `external_id`, `ttclid` — more = higher score
- IP + UA correctly attached
- Hashing correctness

Target ≥ 70. Below 50 usually means missing `ttclid` capture OR phone format wrong (TikTok's no-`+` quirk).

## Common pitfalls

- **Missing trailing slash on endpoint** → 404. `/event/track/` not `/event/track`.
- **Phone with `+`** → matching fails silently. TikTok wants `5511999999999`, not `+5511999999999`.
- **Same `event_id` between platforms** is fine — they each dedup independently. Don't try to make `event_id` unique-per-platform.
- **No `ttp` cookie present** → Pixel didn't load in this session OR consent denied. Send the event without `ttp`; match quality drops but still works if email/phone present.
- **`event_source: "web"` typo as `"website"`** → rejected. It's `web` exactly.
- **Forgetting `event_source_id`** → 400. It's the Pixel ID, required even though it feels redundant with the URL.

## SDK option

No official Node SDK. Use `fetch` directly as in `route.ts` / `tracking-sidecar/server.ts`. Community wrappers exist but they're thin — not worth a dependency.
