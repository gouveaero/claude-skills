# Cookies & Attribution

Every ad platform's match quality hinges on capturing the right cookies on the right edge of the funnel. This file documents what each one is, how it's set, and how the skill's `lib/cookies.ts` handles them.

## The six cookies that matter

| Cookie | Set by | Source | Lifetime | Purpose |
|--------|--------|--------|----------|---------|
| `_fbp` | Meta Pixel JS | First Pixel load | 90 days | 1st-party browser ID; always sent |
| `_fbc` | Our code (or Pixel JS) | `?fbclid=` on landing | 90 days | Click ID; **only set when fbclid present** |
| `_ttp` | TikTok Pixel JS | First Pixel load | 13 months | 1st-party browser ID; always sent |
| `_ttclid` | Our code | `?ttclid=` on landing | 90 days | TikTok click ID; **only set when ttclid present** |
| `_ga` | `gtag.js` | First gtag load | 2 years | GA4 client_id — read via `gtag('get', ...)`, not regex |
| `_gcl_aw` | gtag conversion linker | `?gclid=` on landing | 90 days (configurable to 540) | Google Ads click ID |

## The pattern: set on first arrival, persist, forward server-side

Two of these (`_fbc`, `_ttclid`) the **skill must set manually** — Meta and TikTok pixels do not set them on their own. The skill's `lib/cookies.ts` reads the URL on every page mount, extracts `fbclid` / `ttclid`, and sets the cookie if it's missing:

```ts
// lib/cookies.ts (client-side, runs in useEffect or root component)
export function captureAttributionCookies() {
  if (typeof window === 'undefined') return;
  const params = new URLSearchParams(window.location.search);

  const fbclid = params.get('fbclid');
  if (fbclid && !getCookie('_fbc')) {
    const value = `fb.1.${Date.now()}.${fbclid}`;
    setCookie('_fbc', value, 90);
  }

  const ttclid = params.get('ttclid');
  if (ttclid && !getCookie('_ttclid')) {
    setCookie('_ttclid', ttclid, 90);
  }

  // _gcl_aw is handled by gtag conversion linker automatically if you set
  // `linker: { domains: [...] }` in gtag config. The skill enables it by default.
}
```

`setCookie` writes 1st-party (`Domain=.yourdomain.com`), `SameSite=Lax`, `Path=/`. On HTTPS sites add `Secure`.

## Reading on the server

In Next.js App Router route handler:

```ts
function readCookies(request: Request): Record<string, string> {
  const cookieHeader = request.headers.get('cookie') ?? '';
  return Object.fromEntries(
    cookieHeader.split(';').map(c => {
      const [k, ...v] = c.trim().split('=');
      return [k, decodeURIComponent(v.join('='))];
    }).filter(([k]) => k)
  );
}

const cookies = readCookies(request);
const fbp = cookies._fbp;
const fbc = cookies._fbc;
const ttp = cookies._ttp;
const ttclid = cookies._ttclid;
const gclid = parseGclidFromGclAw(cookies._gcl_aw);  // see below
```

`_gcl_aw` format is `GCL.{ts}.{gclid}` — extract the last segment.

## GA4 client_id — the May 2025 cookie gotcha

The `_ga` cookie format **changed in May 2025** without much announcement. The old way of regex-parsing `_ga` for client_id broke silently for many installs.

**Don't do this** (worked before May 2025, unreliable now):
```ts
const ga = cookies._ga;  // "GA1.2.1234567890.1747000000"
const clientId = ga.split('.').slice(2).join('.');  // breaks on new format
```

**Do this** instead — ask gtag directly:
```ts
function getGa4ClientId(measurementId: string): Promise<string | undefined> {
  return new Promise(resolve => {
    if (!window.gtag) return resolve(undefined);
    window.gtag('get', measurementId, 'client_id', (id: string) => resolve(id));
    setTimeout(() => resolve(undefined), 500);  // fallback if gtag is wedged
  });
}
```

The client gets `client_id` from gtag, passes it in the `/api/track` POST body, server uses it directly. Treats the cookie as opaque.

Source: https://www.trkkn.com/insights/ga4-cookie-format-has-changed-what-you-need-to-know-about-ga-measurement-id-and-session-id/

## `_fbc` formation rule

If `?fbclid=AbCdEf` is in the URL on landing:

```
_fbc = fb.1.{timestamp_in_milliseconds}.{fbclid_value}
```

The `1` is the "subdomain index" — for a site at `yourdomain.com`, it's `1` (root). For `sub.yourdomain.com`, it's `2`. The skill always uses `1` — if a client has multi-subdomain setup, this needs adjustment.

**Critical rule:** never synthesize `_fbc` from nothing. If there's no `fbclid` on landing, there's no `_fbc`, and that's correct — the user didn't arrive from a Meta ad. CAPI handles missing `_fbc` gracefully (lower match quality but still works).

## `_fbp` formation rule

`_fbp = fb.1.{creation_time_millis}.{random_uint}`

Set automatically by the Pixel script on first load. The skill **doesn't generate** `_fbp` — if the Pixel script isn't loaded (e.g. consent denied), there's no `_fbp`, and CAPI still works without it.

## `_ttclid` and `_ttp`

Same pattern as `_fbc` and `_fbp` respectively:
- `_ttclid` is only set when `?ttclid=` is on the URL. Skill code sets it (TikTok Pixel does not).
- `_ttp` is set automatically by TikTok Pixel JS when it loads. Don't try to generate manually.

## Multi-subdomain considerations

Sites that use `app.domain.com` for the app + `www.domain.com` for marketing need cookies on the root domain (`.domain.com`) so both subdomains see the same `_fbp` / `_fbc` etc.

The skill's `setCookie` defaults to root domain. If a client has subdomains, this Just Works. If they're on completely different domains (`leticialang.com` and `leticialang.exosmkt.com`), each domain gets its own cookie jar — that's a tracking gap and the client should consolidate to one root.

## Cross-domain attribution

If the lead capture happens on Domain A but the conversion fires on Domain B (e.g. a separate checkout subdomain or a 3rd-party payment processor), cookies don't transfer.

Mitigation:
1. **gtag linker**: `gtag('config', 'AW-...', { linker: { domains: ['a.com', 'b.com'] } })` decorates outbound links with `_gl=` parameter that gtag picks up on the destination side. Works for Google Ads / GA4 only.
2. **URL param relay**: append `?fbclid={cookie_fbc_part}&ttclid={cookie_ttclid}` to outbound links. Hacky.
3. **Server-side join via `external_id`**: assign a logged-in user a stable `external_id`, pass it in `user_data` on both domains. Server-side, attribution can be reconstructed via `external_id` matching.

The skill's templates do **not** do cross-domain by default. If the user mentions a separate checkout domain, surface this section and propose option 1 or 3.

## Putting it together in the fan-out endpoint

```ts
// app/api/track/route.ts — pseudocode for the server-side enrichment step
const cookies = readCookies(request);
const ip = (request.headers.get('x-forwarded-for') ?? '').split(',')[0].trim() || undefined;
const ua = request.headers.get('user-agent') ?? undefined;

const metaUserData = {
  em: body.params.email ? sha256(normalizeEmail(body.params.email)) : undefined,
  ph: body.params.phone ? sha256(normalizePhoneE164NoPlus(body.params.phone)) : undefined,
  // ... other fields
  fbp: cookies._fbp,           // raw
  fbc: cookies._fbc,           // raw
  client_ip_address: ip,
  client_user_agent: ua,
  external_id: body.params.externalId,
};

const tiktokUser = {
  email: body.params.email ? sha256(normalizeEmail(body.params.email)) : undefined,
  phone: body.params.phone ? sha256(normalizePhoneE164NoPlus(body.params.phone)) : undefined,
  ttclid: cookies._ttclid,     // raw
  ttp: cookies._ttp,           // raw
  ip,                          // raw
  user_agent: ua,              // raw
};

// GA4 client_id comes from the request body (client called gtag('get', ...) before POST)
const ga4ClientId = body.client_id;
```

That's the whole cookie story. Read this file when adding a new platform's identity field or debugging a "match quality dropped" complaint.
