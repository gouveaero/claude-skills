# Meta — Conversions API (CAPI) + Pixel

Read this when the skill needs to generate Meta-specific code (Pixel `fbq` init, CAPI fan-out function, hashing, dedup). The companion client-side library lives in [`assets/<stack>/lib/track.ts`](../assets/) and the fan-out function in `app/api/track/route.ts` (Next) or `tracking-sidecar/server.ts` (Vite).

## Endpoint

```
POST https://graph.facebook.com/{GRAPH_VERSION}/{PIXEL_ID}/events?access_token={CAPI_TOKEN}
Content-Type: application/json
```

- `GRAPH_VERSION` lives in `.env` as `META_GRAPH_VERSION` (default `v25.0`, released Feb 2026 alongside Marketing API v25). **Never hardcode** — Meta deprecates versions on ~2-year cycle. Changelog: https://developers.facebook.com/docs/graph-api/changelog/versions/
- `PIXEL_ID` lives in `.tracking.json` as `platforms.meta.pixel_id` (a string of digits).
- `CAPI_TOKEN` lives in `.env.local` / Coolify env vars. Never in code. Generated in Events Manager → Settings → Conversions API → Generate Access Token.

## Top-level body

```json
{
  "data": [ /* ServerEvent[] — see below */ ],
  "test_event_code": "TEST12345",
  "partner_agent": "tracking-pixels-skill-v1"
}
```

- `data[]` accepts up to 1000 events per call but **batch 10–50 in practice**. Validation is all-or-nothing — one bad event rejects the whole batch.
- `test_event_code` is **only** used during testing — pull it from `META_TEST_EVENT_CODE` env var, leave empty in production. Code is generated in Events Manager → Test Events.
- `partner_agent` should identify your integration. Use `tracking-pixels-skill-v1` (or include the client code).

## ServerEvent shape

```ts
type ServerEvent = {
  event_name: string;          // e.g. "Lead", "Purchase" — must match Pixel exactly
  event_time: number;          // unix seconds
  event_id: string;            // dedup key — SAME uuid as fbq's eventID
  action_source: 'website' | 'email' | 'app' | 'phone_call' | 'chat' | 'physical_store' | 'system_generated' | 'other';
  event_source_url: string;    // full URL of the page
  user_data: UserData;         // see hashing rules below
  custom_data?: CustomData;    // value, currency, content_ids, content_type, contents[]
  data_processing_options?: string[];           // ['LDU'] for California etc.
  data_processing_options_country?: number;     // 0 = auto-detect
  data_processing_options_state?: number;       // 0 = auto-detect
};
```

For most web tracking: `action_source: 'website'`.

## Standard events (use these names exactly — case-sensitive)

`PageView`, `ViewContent`, `Search`, `AddToCart`, `AddToWishlist`, `InitiateCheckout`, `AddPaymentInfo`, `Purchase`, `Lead`, `CompleteRegistration`, `Contact`, `CustomizeProduct`, `Donate`, `FindLocation`, `Schedule`, `StartTrial`, `SubmitApplication`, `Subscribe`.

Custom events (any other string) are fine but lose Advantage+ optimization signal.

## `user_data` — hashing rules (SHA-256, hex, lowercase)

Normalize → SHA-256 → hex string → lowercase, for these fields:

| Field | Normalization (before hash) |
|-------|-----------------------------|
| `em` | lowercase, trim |
| `ph` | E.164 digits only, no `+` — e.g. `5511999999999` |
| `fn` / `ln` | lowercase, strip punctuation, trim |
| `db` | `YYYYMMDD` (8 digits) |
| `ge` | `m` or `f` (lowercase) |
| `ct` | lowercase, strip spaces/punctuation |
| `st` | 2-letter state code, lowercase (e.g. `sp`) |
| `zp` | lowercase, hyphens OK |
| `country` | ISO-2 lowercase (e.g. `br`) |
| `external_id` | recommended hashed, optional raw |

**Do NOT hash:** `client_ip_address`, `client_user_agent`, `fbc`, `fbp`, `subscription_id`, `fb_login_id`. These go raw.

The skill's `lib/hash.ts` does this — read it instead of reimplementing.

Spec: https://developers.facebook.com/docs/marketing-api/conversions-api/parameters/customer-information-parameters

### `external_id` and Event Match Quality (EMQ)

Sending a hashed `external_id` is one of the cheaper EMQ wins after `em`/`ph` (email ≈ +4 points, phone ≈ +3). Rules of thumb:

- Use a **stable internal ID** — CRM contact ID, lead ID, database user ID. Never email or phone repackaged as external_id (those already have their own fields).
- The same ID must be sent consistently across events for the same person, or it hurts instead of helps.
- The templates already hash and forward `params.externalId` — call sites just need to pass it when the form/CRM produces one (e.g. the GrowAI/CRM lead ID returned on submit).

## `_fbc` and `_fbp` cookies

- **`_fbp`** is auto-created by the Pixel script. Format: `fb.1.{creation_millis}.{random_uint}`. 90-day lifetime, 1st-party. The server just **reads and forwards it raw**.
- **`_fbc`** is **only created when `?fbclid=...` is present in the URL**. Format: `fb.1.{ts_millis}.{fbclid_value}`. Never synthesize from nothing — that breaks attribution. Capture on first arrival, persist 90 days.

The skill's `lib/cookies.ts` handles both. If the user disables the Pixel client-side (`fbq` doesn't load), the cookies won't exist — that's fine, CAPI works without them but with weaker match quality.

## Deduplication — the 48h window

Meta dedups events when **both** `event_id` AND `event_name` match across Pixel + CAPI within a **48-hour window**. The server-side event is preferred (more reliable, has IP/UA).

Implementation rule: **generate `event_id` once on the client, mirror it on the server.**

```ts
// Client (lib/track.ts) — already generates event_id
const event_id = crypto.randomUUID();
window.fbq?.('track', 'Lead', { value: 100, currency: 'BRL' }, { eventID: event_id });
fetch('/api/track', { body: JSON.stringify({ name: 'Lead', event_id, ... }) });

// Server (route.ts) — uses the SAME event_id
data: [{ event_name: 'Lead', event_id, /* ... */ }]
```

Refs: https://developers.facebook.com/docs/marketing-api/conversions-api/deduplication

## Test events flow

1. Events Manager → Test Events tab → copy the `TEST*****` code.
2. Set `META_TEST_EVENT_CODE=TEST12345` in `.env.local`.
3. Fire an event from your local dev. Within ~30 seconds it appears in the Test Events tab with the dedup badge if Pixel + CAPI both fired.
4. **Remove the env var in production** — leaving `test_event_code` in real traffic means those events don't show up in reports.

## `client_ip_address` + `client_user_agent`

Always send these (raw) on the server side. They're Meta's strongest match signals after `em`/`ph`. In Next.js App Router:

```ts
const ip = request.headers.get('x-forwarded-for')?.split(',')[0].trim()
        ?? request.headers.get('x-real-ip')
        ?? undefined;
const ua = request.headers.get('user-agent') ?? undefined;
```

In Vite sidecar (Express/Fastify/Bun.serve): same headers, framework-specific accessor.

## LDU (Limited Data Use, US states)

For CA / CO / CT users, Meta requires LDU mode. Set per-event:

```json
{
  "data_processing_options": ["LDU"],
  "data_processing_options_country": 0,
  "data_processing_options_state": 0
}
```

`0, 0` = let Meta auto-detect country/state from IP. **LDU is not a GDPR/LGPD solution** — for Brazilian users we don't typically set it. If the client is a US-focused brand, enable LDU by default in the fan-out function.

Spec: https://developers.facebook.com/docs/meta-pixel/implementation/data-processing-options

## Error responses

CAPI returns 200 even when individual events are invalid — check the body:

```json
{
  "events_received": 1,
  "messages": [],
  "fbtrace_id": "AbCdEf..."
}
```

Or on failure:

```json
{
  "error": {
    "message": "Invalid parameter",
    "type": "OAuthException",
    "code": 100,
    "fbtrace_id": "..."
  }
}
```

The fan-out function should log `fbtrace_id` so debugging in Events Manager → Diagnostics is possible.

## Common pitfalls (compiled from real installs)

- **Pixel + CAPI sending different `event_name` casing** — `Lead` vs `lead` don't dedup. Always exact match.
- **Forgetting `external_id` is hashed** — sending raw user IDs breaks audience matching down the line.
- **Phone with `+` or formatting** — Meta strips it but matching gets unreliable. Pre-normalize to E.164 digits.
- **Hashing on the client** — don't. The browser sends raw to your `/api/track`, server hashes once. Hashing twice = no match.
- **Time skew** — `event_time` must be ≤ 7 days in the past. For real-time events, use `Math.floor(Date.now() / 1000)`.

## SDK option (not used in templates)

`facebook-nodejs-business-sdk` (v25.x, official) wraps all this with classes (`ServerEvent`, `UserData`, `CustomData`, `EventRequest`). The skill's templates **don't use it** — they `fetch` directly to avoid pulling in the SDK's dependency tree. If a client specifically wants the SDK (e.g. for batch operations beyond CAPI), add it later.

Reference repo for SDK-based Next.js: https://github.com/RivercodeAB/facebook-conversion-api-nextjs
