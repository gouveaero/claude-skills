# Google Ads — Enhanced Conversions (Web + Leads)

Read this when the skill needs to wire Google Ads conversion tracking. There are two flavors and they're often confused:

| Mode | When | How |
|------|------|-----|
| **Enhanced Conversions for Web** | Conversion happens on-site (purchase, signup) | `gtag('set', 'user_data', {...})` + `gtag('event', 'conversion', {send_to})` on the client |
| **Enhanced Conversions for Leads** | Conversion happens off-site (sales rep closes a lead by phone) | Lead form fires gtag (captures `gclid` + user_data); later, you upload the closed-won conversion via Google Ads API `ConversionAdjustmentService` matching on hashed email/phone |

The skill's default install does **EC for Web** (client-side `gtag`). EC for Leads requires CRM integration that's out of scope — the skill notes it as a follow-up if the client mentions offline sales.

## Configuration in `.tracking.json`

```json
"google_ads": {
  "enabled": true,
  "conversion_id": "AW-123456789",
  "conversion_labels": {
    "Lead": "abc123/xyz",
    "Purchase": "abc123/qrs",
    "Schedule": "abc123/sch"
  }
}
```

`conversion_id` is shared per Google Ads account. `conversion_labels` is one label per event type, generated in Google Ads → Tools → Conversions → New conversion action.

## Client-side install (EC for Web)

In `components/PixelBootstrap.tsx`, load `gtag.js` once:

```tsx
<Script
  src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GOOGLE_ADS_CONVERSION_ID}`}
  strategy="afterInteractive"
/>
<Script id="gads-init" strategy="afterInteractive">{`
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  window.gtag = gtag;
  gtag('js', new Date());
  gtag('config', '${process.env.NEXT_PUBLIC_GOOGLE_ADS_CONVERSION_ID}', { allow_enhanced_conversions: true });
`}</Script>
```

When firing a conversion in `lib/track.ts`:

```ts
// 1. Set user_data BEFORE the conversion event (this is what makes it "enhanced")
window.gtag?.('set', 'user_data', {
  email: params.email,                // gtag will hash on send
  phone_number: params.phone,         // E.164 with +
  address: {
    first_name: params.firstName,
    last_name: params.lastName,
    postal_code: params.postalCode,
    country: params.country,
  },
});

// 2. Fire the conversion
window.gtag?.('event', 'conversion', {
  send_to: `${conversionId}/${conversionLabels[name]}`,
  value: params.value,
  currency: params.currency ?? 'BRL',
  transaction_id: event_id,           // dedup across web + offline upload
});
```

**`send_to: 'AW-{id}/{label}'`** — without the label, the event counts as remarketing only, NOT a conversion. Common mistake.

**Pre-hashing** (optional): `gtag` hashes user_data on send by default. If you want to hash server-side and pass the digest, use the variants:

```ts
gtag('set', 'user_data', {
  sha256_email_address: '<hex>',
  sha256_phone_number: '<hex>',
  sha256_first_name: '<hex>',
  sha256_last_name: '<hex>',
});
```

The skill's templates use the **raw fields** (let gtag hash) — simpler, and gtag's hashing matches Google's expected normalization exactly.

## Normalization (when pre-hashing server-side)

- Email: lowercase + trim. Then SHA-256 hex lowercase.
- Phone: E.164 with leading `+` (e.g. `+5511999999999`). Then SHA-256 hex lowercase.
- Name: lowercase, trim, strip diacritics, no punctuation. Then SHA-256 hex lowercase.
- Postal code: lowercase, alphanumeric. Then SHA-256 hex lowercase.
- Country: ISO-2 uppercase (e.g. `BR`). NOT hashed.

Spec: https://support.google.com/google-ads/answer/13262500

## Required fields for matching

At least one of:
- `email` (preferred — best match rate)
- `phone_number`
- Full address: `first_name` + `last_name` + `postal_code` + `country`

A form with only "name + email" → send email. A form with name + phone but no email → send phone. The skill should pass whatever it has from the form into `params` and the gtag call handles partials gracefully.

## EC for Leads (offline upload — out of scope for default install)

When a lead becomes a customer days later via a sales call:

1. Frontend logged the lead via `gtag('event', 'conversion', ...)` with `transaction_id: event_id`. Google captures the `gclid` from the cookie automatically.
2. Sales rep marks the deal as won in CRM. Webhook fires to your backend.
3. Backend calls Google Ads API `ConversionAdjustmentService.uploadCallConversions` (or `uploadClickConversions`) with `gclid` + hashed `email`/`phone` + `conversion_action_id` + `conversion_value`.
4. Google attributes the conversion to the original ad click.

Library: `google-ads-nodejs-client` (official) or `google-ads-api` (community). Auth via OAuth2 + developer token + login customer ID.

Reference: https://support.google.com/google-ads/answer/11021502

The skill **does not** generate this — it's a CRM-specific integration that depends on the client's stack (HubSpot? Pipedrive? Notion? custom DB?). If the user asks for EC for Leads, suggest opening a follow-up task and link this section.

## Unification (April 2026)

Google is unifying EC for Web + EC for Leads into a single toggle in Google Ads UI. After April 2026, you turn on "Enhanced Conversions" once and both flavors are available — the site tags, Data Manager imports, and API uploads can all coexist for the same conversion action. Skill behavior doesn't change (we always set `user_data`); only the UI explanation gets simpler.

Source: https://support.google.com/google-ads/answer/13258081

## Debug

- **Tag Assistant Chrome extension** — shows `gtag('event','conversion')` calls + whether user_data was set.
- **Google Ads → Tools → Diagnostics** — Enhanced Conversions tab shows match rate per conversion action (target ≥ 75% within 7 days of activation).
- **Network tab** — look for `POST https://www.google-analytics.com/g/collect?v=2&tid=AW-...` (yes, gtag uses GA's `g/collect` for Ads conversions too).

## Common pitfalls

- **Forgetting `send_to` label** — counts as remarketing, not conversion. Always `AW-ID/LABEL`.
- **Setting `user_data` AFTER the conversion event** — must be before, otherwise gtag doesn't include it.
- **Phone without `+`** — Google's normalization expects E.164 with the leading `+`. Don't strip it (Meta does, Google doesn't).
- **`transaction_id` collisions on `Purchase`** — Google dedups purchases by `transaction_id` for 90 days. Use `event_id` (UUID) and you're fine. Don't reuse `order_id` if the same order can be refunded + repurchased.
- **No conversion fires** despite `gtag` returning ok — check that the user has accepted cookies/consent if you have a banner; gtag respects `gtag('consent', 'default', {...})` modes.
