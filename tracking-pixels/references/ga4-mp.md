# GA4 — Measurement Protocol (server-side) + gtag (client-side)

GA4 lives on a different mental model than Meta/TikTok: it's an **analytics property** first, with optional ad-side enhancement (audiences exported to Google Ads). The skill installs both:

1. **`gtag.js` on the client** — handles `page_view`, scroll, click, etc. via Enhanced Measurement; user-fired events via `gtag('event', name, params)`.
2. **Measurement Protocol on the server** — fires the same event from the backend with the **same `client_id`** so it merges into the same session.

## Endpoints

```
POST https://www.google-analytics.com/mp/collect?measurement_id={G-XXXXXXX}&api_secret={SECRET}
# EU region:
POST https://region1.google-analytics.com/mp/collect?measurement_id=...&api_secret=...

# Debug (validates without writing):
POST https://www.google-analytics.com/debug/mp/collect?...
# Returns { validationMessages: [...] }
```

- `measurement_id` is public (`G-XXXXXXX`). Lives in `.tracking.json` as `platforms.ga4.measurement_id`.
- `api_secret` is sensitive. Lives in env var `GA4_API_SECRET`. Generated in GA4 → Admin → Data Streams → your stream → Measurement Protocol API secrets → Create.

Spec: https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference

## Body shape

```json
{
  "client_id": "1234567890.1747000000",
  "user_id": "internal-user-id",
  "timestamp_micros": 1747000000000000,
  "non_personalized_ads": false,
  "events": [
    {
      "name": "generate_lead",
      "params": {
        "currency": "BRL",
        "value": 100,
        "transaction_id": "<event_id>",
        "session_id": "1747000000",
        "engagement_time_msec": 1
      }
    }
  ]
}
```

- `client_id` is **required**. It must match what `gtag.js` set in the browser, or you fragment the user.
- `user_id` is optional but recommended for logged-in users (your internal ID, NOT email).
- `timestamp_micros` defaults to now if omitted. Events can be **backdated at most 72 hours** — older timestamps are dropped.
- `engagement_time_msec` is needed for the event to show up in standard reports (otherwise it's "non-engaged" and many reports filter it out). Minimum `1`.
- `session_id` (event param) is **strongly recommended** — see the session-stitching section below.

## Limits

- 25 events per request
- 25 params per event
- 100-char limit per param value (500 in GA360)
- 130 KB total payload

## Reserved event names — do NOT use

GA4 silently drops events with these names. Use a different name (the skill maps Meta's `PageView` → `page_view`, Meta's `Lead` → `generate_lead`, etc.).

`ad_activeview`, `ad_click`, `ad_exposure`, `ad_query`, `ad_reward`, `adunit_exposure`, `app_clear_data`, `app_exception`, `app_install`, `app_remove`, `app_store_refund`, `app_store_subscription_cancel`, `app_store_subscription_convert`, `app_store_subscription_renew`, `app_update`, `app_upgrade`, `dynamic_link_app_open`, `dynamic_link_app_update`, `dynamic_link_first_open`, `error`, `firebase_campaign`, `firebase_in_app_message_action`, `firebase_in_app_message_dismiss`, `firebase_in_app_message_impression`, `first_open`, `first_visit`, `in_app_purchase`, `notification_dismiss`, `notification_foreground`, `notification_open`, `notification_receive`, `notification_send`, `os_update`, `session_start`, `user_engagement`.

App-only (don't use in web): `ad_impression`, `in_app_purchase`, `screen_view` (use `page_view` instead).

## Recommended event names (GA4 standard)

`page_view`, `view_item`, `select_item`, `view_item_list`, `add_to_cart`, `remove_from_cart`, `view_cart`, `begin_checkout`, `add_payment_info`, `add_shipping_info`, `purchase`, `refund`, `generate_lead`, `sign_up`, `login`, `search`, `share`, `select_promotion`, `view_promotion`.

## Cross-platform name mapping (the skill does this automatically)

| Universal name | Meta `event_name` | GA4 `events[].name` | TikTok `event` |
|----------------|-------------------|---------------------|----------------|
| `PageView` | `PageView` | `page_view` | `Browse` |
| `Lead` | `Lead` | `generate_lead` | `SubmitForm` |
| `Purchase` | `Purchase` | `purchase` | `CompletePayment` |
| `InitiateCheckout` | `InitiateCheckout` | `begin_checkout` | `InitiateCheckout` |
| `AddPaymentInfo` | `AddPaymentInfo` | `add_payment_info` | `AddPaymentInfo` |
| `Schedule` | `Schedule` | `schedule` (custom) | `ClickButton` |
| `Contact` | `Contact` | `contact` (custom) | `Contact` |
| `CompleteRegistration` | `CompleteRegistration` | `sign_up` | `CompleteRegistration` |

## `client_id` — the cookie format change (May 2025)

**Heads-up:** Google changed the `_ga` cookie format in May 2025 without much warning. Many setups that did regex parsing of `_ga` broke silently.

**Old format:** `_ga = GA1.2.{client_id_p1}.{client_id_p2}` — you could extract `client_id` as `${p1}.${p2}`.

**New format (post-May 2025):** parsing on the client cookie is unreliable.

**Solution the skill uses:** call gtag's getter API instead of touching the cookie.

```ts
// lib/cookies.ts (client-side helper)
export function getGa4ClientId(measurementId: string): Promise<string | undefined> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined' || !window.gtag) return resolve(undefined);
    window.gtag('get', measurementId, 'client_id', (id: string) => resolve(id));
    setTimeout(() => resolve(undefined), 500); // fallback if gtag is wedged
  });
}
```

The skill calls this client-side, attaches the result to the `/api/track` POST body, and the server uses it directly in the MP payload.

Source: https://www.trkkn.com/insights/ga4-cookie-format-has-changed-what-you-need-to-know-about-ga-measurement-id-and-session-id/

## `session_id` — session stitching

MP events that arrive without a `session_id` param land **session-less**: they don't attach to the user's live session, which breaks session-scoped reports and attribution (the event shows up under "(not set)" sessions). Always send it alongside `client_id`.

**Capture (client-side)** — same getter pattern as `client_id`:

```ts
// lib/cookies.ts — getGa4SessionId(measurementId)
window.gtag('get', measurementId, 'session_id', (id) => resolve(String(id)));
// Fallback if gtag is wedged: parse the _ga_<CONTAINER> cookie
// (CONTAINER = measurement id minus "G-"):
//   pre-May-2025:  "GS1.1.<session_id>.<n>..."
//   current:       "GS2.1.s<session_id>$o<n>$..."
// Regex used by the skill: /^GS\d\.\d\.s?(\d{9,11})/
```

**Forward (server-side)** — as an event param, guarded by MP's format requirement:

- MP requires `session_id` to match **`^\d+$`** (numeric string). Never forward the raw `GS2.1.s...` cookie value — extract the digits.
- The skill's fan-out validates with the regex before including it; a malformed value is dropped silently rather than poisoning the payload.

Sending a custom `session_id` can also create a session server-side (no `session_start` needed), but for the skill's use case the goal is always to **stitch into the browser session**, so the gtag getter value wins.

**Scope note:** MP is a *supplement* to gtag, not a replacement — Google's own guidance. The browser tag remains the source of sessions, consent state, and Enhanced Measurement; MP adds the ad-blocker-proof server copy.

## Server-side fan-out template

```ts
async function sendToGa4(args: {
  measurementId: string;
  apiSecret: string;
  clientId: string;
  sessionId?: string;
  userId?: string;
  eventName: string;
  eventTimeMicros: number;
  params: Record<string, unknown>;
}) {
  const url = `https://www.google-analytics.com/mp/collect?measurement_id=${args.measurementId}&api_secret=${args.apiSecret}`;
  const body = {
    client_id: args.clientId,
    user_id: args.userId,
    timestamp_micros: args.eventTimeMicros,
    events: [{
      name: args.eventName,
      params: {
        engagement_time_msec: 1,
        // session stitching — only if numeric (MP requirement)
        ...(args.sessionId && /^\d+$/.test(args.sessionId) ? { session_id: args.sessionId } : {}),
        ...args.params,
      },
    }],
  };
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  // MP returns 204 No Content on success. Errors are silent — use /debug/mp/collect for validation.
  return { status: res.status };
}
```

## DebugView

Set `debug_mode: true` in the params OR include `_dbg: 1` in any param to make events show up in GA4 → Configure → DebugView in near-real-time. The skill's templates expose `DEBUG_GA4=1` env var that flips this on.

## User data on GA4 (Ads-linked)

If GA4 is linked to a Google Ads account, you can include `user_data` in the MP event to enrich audiences:

```json
"params": {
  "user_data": {
    "email_address": "<sha256_hex>",
    "phone_number": "<sha256_hex>",
    "address": { "first_name": "<sha256_hex>", "last_name": "<sha256_hex>" }
  }
}
```

Same hashing rules as Google Ads (SHA-256 hex lowercase, E.164 phone with `+`). The skill's `lib/hash.ts` does this.

## Common pitfalls

- **`client_id` mismatch** between gtag (browser) and MP (server) → looks like 2 different users. Always pass through the `_ga`-derived ID via `gtag('get', ...)`.
- **No `session_id`** → event lands session-less, breaks session-scoped reports/attribution. Capture via `gtag('get', ..., 'session_id', cb)` and forward (numeric string only).
- **No `engagement_time_msec`** → event hidden from many reports. Always include `engagement_time_msec: 1` minimum.
- **Sending reserved event names** → silently dropped. Always map (table above).
- **Test events polluting Realtime** without filter → use Internal Traffic filter in GA4 Admin to exclude your dev IP.
- **Forgetting EU region endpoint** if the data stream is EU-based → minor latency, no functional issue, but Google recommends `region1.` for EU traffic.
