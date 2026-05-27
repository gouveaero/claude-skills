# LGPD / GDPR Consent — opt-in mode

By default the skill installs tracking with **no consent gating**. Most Exos clients are B2C / professional services where the user implicitly opts in by submitting the form. If the client needs strict compliance (regulated industries, EU traffic, sensitive verticals), invoke the **`enable-lgpd`** mode.

## When the user needs this

Triggers to switch to LGPD mode:
- Client is in a regulated profession (medicine in some specialties, finance, education with minors).
- Site has EU traffic and the client doesn't want to filter EU users out.
- Client's legal team specifically asked for cookie consent.
- Client is large enough that LGPD enforcement risk is non-trivial (~R$ 50k+ revenue/month).

If none of these apply, default mode is correct. The user can always switch later — `enable-lgpd` is additive.

## What `enable-lgpd` mode does

Three changes to a default install:

1. **Edits `.tracking.json`**: sets `consent.lgpd_mode: "gated"` and `consent.default_state: "denied"` (the safe default — pixels off until user clicks Accept).
2. **Copies the consent banner asset**: drops `assets/lgpd-consent-banner.tsx` into `components/ConsentBanner.tsx`. Mounts it inside `<PixelBootstrap />`.
3. **Modifies `lib/track.ts` and `components/PixelBootstrap.tsx`** to read `consent-state` cookie and gate behavior.

## The consent gate pattern

In `PixelBootstrap.tsx`:

```tsx
'use client';
import { useEffect, useState } from 'react';
import Script from 'next/script';
import { ConsentBanner } from './ConsentBanner';

export function PixelBootstrap() {
  const [consent, setConsent] = useState<'pending' | 'granted' | 'denied'>('pending');

  useEffect(() => {
    const stored = document.cookie.split(';').find(c => c.trim().startsWith('consent-state='));
    if (stored) {
      setConsent(stored.split('=')[1].trim() as 'granted' | 'denied');
    }
  }, []);

  if (consent === 'pending') {
    // Pre-consent: Meta Pixel can load in "consent revoked" mode (no cookies set, no events fired)
    return (
      <>
        <Script id="fbq-init" strategy="afterInteractive">{`
          !function(f,b,e,v,n,t,s){...}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
          fbq('consent', 'revoke');
          fbq('init', '${pixelId}');
        `}</Script>
        <ConsentBanner onGrant={() => setConsent('granted')} onDeny={() => setConsent('denied')} />
      </>
    );
  }

  if (consent === 'denied') {
    return null;  // pixels do not load
  }

  // Granted — full load
  return (
    <>
      <Script id="fbq-init" strategy="afterInteractive">{`
        !function(f,b,e,v,n,t,s){...}(...);
        fbq('init', '${pixelId}');
        fbq('consent', 'grant');
        fbq('track', 'PageView');
      `}</Script>
      {/* GA4, TikTok loads here too */}
    </>
  );
}
```

The pattern uses Meta's native consent API (`fbq('consent', 'revoke' | 'grant')`) — the Pixel loads in revoked mode so its JS is present but doesn't set cookies or fire events. When the user accepts, `fbq('consent', 'grant')` flips the switch.

Spec: https://developers.facebook.com/docs/meta-pixel/implementation/gdpr

## Server-side behavior under consent denial

When `consent-state === 'denied'`, the client still POSTs to `/api/track` (the network request is unavoidable since we share JS), but it sends a `consent: 'denied'` flag in the body. The server then sends a **minimal anonymous event** to Meta CAPI:

```ts
// Server-side: consent denied → strip PII
const userData = body.consent === 'denied'
  ? { client_ip_address: ip, client_user_agent: ua }  // only the bare minimum
  : { /* full hashed em/ph/fn/ln + fbp/fbc/ip/ua */ };
```

For GA4 / TikTok / Google Ads under denied consent: skill skips the fan-out entirely. Meta is the only one where an "anonymous" event has value (Advantage+ optimization can still use the IP/UA signal even without PII).

## GA4 Consent Mode

If the client uses Google's official Consent Mode v2:

```ts
gtag('consent', 'default', {
  ad_storage: 'denied',
  analytics_storage: 'denied',
  ad_user_data: 'denied',
  ad_personalization: 'denied',
  wait_for_update: 500,
});

// On user accept:
gtag('consent', 'update', {
  ad_storage: 'granted',
  analytics_storage: 'granted',
  ad_user_data: 'granted',
  ad_personalization: 'granted',
});
```

This is the more granular path (separate consent for analytics vs ads). The `enable-lgpd` mode supports this via `.tracking.json`:

```json
"consent": {
  "lgpd_mode": "gated",
  "granular": true,
  "default_state": "denied"
}
```

When `granular: true`, the consent banner shows 4 toggles (analytics, ads, personalization, user_data) instead of a single Accept/Deny.

## TikTok consent

TikTok's Pixel responds to `ttq.disableCookie()` / `ttq.enableCookie()`. Same pattern as Meta:

```ts
// Pre-consent
ttq.load(pixelId);
ttq.disableCookie();

// On accept
ttq.enableCookie();
ttq.page();
```

## LDU (US states) — separate from LGPD

`fbq('dataProcessingOptions', ['LDU'], 0, 0)` is required for California, Colorado, Connecticut users under US state privacy laws. **It does not substitute for LGPD/GDPR** — they're different regulatory regimes. Most Brazilian Exos clients don't need LDU. If the client has US traffic, set it via `.tracking.json`:

```json
"consent": {
  "ldu_us_states": true
}
```

The fan-out function then adds `data_processing_options: ['LDU']` to Meta events per-event.

## Banner UX (`assets/lgpd-consent-banner.tsx`)

The skill ships a minimal, accessible banner:
- Fixed bottom-of-screen, ~80px tall, doesn't trap users (Esc dismisses → counts as denial).
- Three buttons: "Aceitar tudo", "Recusar não-essenciais", "Personalizar" (the third opens the granular modal if `granular: true`).
- Localized PT/EN via a small dict in the component.
- Cookie set: `consent-state=granted|denied`, 365-day expiry, `SameSite=Lax`.

Visual style is intentionally generic Tailwind — clients with strong design systems will want to restyle. The skill notes this in the post-install checklist.

## Common pitfalls

- **Loading the Pixel BEFORE checking consent** → cookies get set before user has a chance to accept. The skill's gate runs BEFORE `fbq('init', ...)` — verify in DevTools that `_fbp` doesn't exist until consent is granted.
- **Treating consent as a single bit** → some users want analytics but not ads. Use `granular: true` if the client is regulated.
- **Forgetting server-side enforcement** → client gates only the JS pixels; server still receives the POST and could send full PII. The skill's `consent === 'denied'` server branch strips PII.
- **Cookie banner blocks LCP** → make sure the banner is rendered with `position: fixed`, `z-index: 50`, not part of the document flow. The shipped banner does this.
- **Consent re-prompt every 7 days due to ITP** → Safari truncates JS-set cookies to 7 days. For LGPD compliance, the consent state cookie should ideally be HTTP-only set by the server on accept. The shipped banner does this via a `POST /api/consent` that the server uses to set `consent-state` with `HttpOnly` + 365-day expiry.
