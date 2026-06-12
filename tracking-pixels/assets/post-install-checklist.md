# Post-install checklist

Run through this list immediately after the skill finishes copying files. Don't claim "tracking is live" until every relevant item is green.

## 1. Local secrets (`.env.local`)

- [ ] `.env.local` exists at the site root (gitignored).
- [ ] Every env var named in `.tracking.json` has a value in `.env.local`.
- [ ] `META_CAPI_TOKEN` starts with `EAA...` and is ≥ 100 chars (anything shorter is a UI display truncation — re-copy).
- [ ] `GA4_API_SECRET` is a 22-character base64-ish string.
- [ ] `TIKTOK_ACCESS_TOKEN` is a long hex-like string.
- [ ] `META_TEST_EVENT_CODE` is set during testing, **empty in production**.

## 2. Build sanity

```bash
# Next.js:
npm run build   # or bun run build
# Vite:
bun run build
```

- [ ] Build succeeds with no errors.
- [ ] No `process.env.UNDEFINED_VAR` warnings.
- [ ] `lib/track.ts` is tree-shaken into the client bundle.

## 3. Local dev smoke test

Start the dev server, open browser, fire 1 PageView + 1 Lead manually.

```bash
# Next.js:
npm run dev
# Vite:
bun dev
```

- [ ] Browser DevTools → Network tab → `POST /api/track` returns 204.
- [ ] Response headers include `X-Track-Status: meta=ok,ga4=ok,tiktok=ok` (or whichever platforms enabled).
- [ ] Browser console: no errors from `fbq`, `gtag`, `ttq`.

## 4. Meta Events Manager — Test Events tab

Set `META_TEST_EVENT_CODE` to the code shown in Test Events tab, restart dev server.

- [ ] PageView arrives in Test Events within ~30s of firing.
- [ ] Each event shows **both** "Browser" and "Server" source badges.
- [ ] Deduplication badge says "Deduplicated" (NOT "Not deduplicated" — that means `event_id` mismatch).
- [ ] User info badges show: `em` ✅, `ph` ✅ (if available), `fbp` ✅, `client_ip_address` ✅, `client_user_agent` ✅.

If dedup says "Not deduplicated":
- Check that `event_id` in browser `Network → Headers → Request Payload` matches the one in Meta's Server event detail.
- Check that `event_name` casing matches exactly (`Lead` not `lead`).

## 5. GA4 DebugView

In `.env.local`, set `DEBUG_GA4=1` (or whatever the skill exposed). In GA4 Admin, ensure your IP isn't excluded (Internal Traffic filter).

Open GA4 → Configure → DebugView.

- [ ] PageView arrives within seconds.
- [ ] User stream count increments by 1.
- [ ] `transaction_id` is populated on Lead events (and Purchase, only if sales events were explicitly opted in — see SKILL.md scope rule).
- [ ] `session_id` is populated on MP events (session stitching — see references/ga4-mp.md).
- [ ] Reserved event names (`session_start`, `first_visit`) are NOT in your custom events list (those are GA4's automatic events).

## 6. TikTok Events Manager — Test Event tab

Set `TIKTOK_TEST_EVENT_CODE`. Fire events.

- [ ] Events appear within ~30s.
- [ ] Match quality badge shows ≥ 70 (Settings → Diagnostics).
- [ ] If `ttclid` is in the URL (`?ttclid=abc`), the test event shows `ttclid: abc`.

## 7. Production deploy

- [ ] Removed `META_TEST_EVENT_CODE`, `TIKTOK_TEST_EVENT_CODE`, `DEBUG_GA4` from Coolify env vars.
- [ ] Public env vars (`NEXT_PUBLIC_*` for Next, `VITE_*` for Vite) added to Coolify with "Is Build Time?" checked.
- [ ] Server-only env vars added without "Is Build Time?".
- [ ] Triggered a redeploy after env var changes (Coolify doesn't auto-redeploy on env changes).
- [ ] Production URL responds to `POST /api/track` with 204 (use curl from your laptop).

## 8. Production sanity (24h check)

After 24 hours of real traffic:

- [ ] Meta Events Manager → Overview: events have non-zero count, dedup rate ≥ 80% (per event type).
- [ ] GA4 → Realtime: users are streaming in.
- [ ] GA4 → Engagement → Events: your custom events (generate_lead, etc.) are listed with counts.
- [ ] TikTok Events Manager → Overview: events counted, no warnings.
- [ ] Google Ads → Tools → Conversions → Settings → Status: conversions are firing (this can take 24-48h to populate).

## 9. Coolify-specific

- [ ] App in Coolify has all env vars set (cross-check against `.env.example`).
- [ ] If sidecar (Vite SPA): the `<client>-tracking` app is deployed and responding at its `track.*` subdomain.
- [ ] If sidecar: CORS works — main site can POST to `track.*` without browser errors.
- [ ] Coolify watchdog isn't restarting the container repeatedly (`docker ps | grep <client>` — uptime should be hours, not minutes).

## 10. Documentation handoff

- [ ] Updated client's `<ClientFolder>/README.md` with: which platforms are tracked, where `.tracking.json` lives, link to this checklist for next-time troubleshooting.
- [ ] If LGPD mode is enabled: documented the consent banner UX for the client's legal review.

---

## When something doesn't work

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `/api/track` returns 500 | Missing env var on server | Check Coolify logs, fill the var, redeploy |
| Meta Test Events shows "Not deduplicated" | `event_id` mismatch between Pixel + CAPI | Verify `lib/track.ts` passes `event_id` to both `fbq` (as `eventID`) and the `/api/track` POST body |
| Match quality < 50 on Meta | Missing `_fbp`/`_fbc` cookies | Confirm Pixel JS is loading (DevTools → Application → Cookies) |
| GA4 events fire but don't show in reports | Missing `engagement_time_msec` param | Check that server-side MP payload includes `engagement_time_msec: 1` |
| TikTok diagnostics shows "No events received" | `event_source: "website"` typo | Should be `"web"` exactly |
| Lots of duplicate purchases in GA4 | `transaction_id` reuse — or site-side Purchase firing alongside the checkout platform's purchase event | Use `event_id` (UUID) not `order_id`; remember site-side Purchase is opt-in (SKILL.md scope rule) |
| GA4 MP events show under "(not set)" sessions | Missing `session_id` param | Confirm `track.ts` captures it via `gtag('get', ..., 'session_id')` and the server forwards it (numeric string) |
| Pixel fires but CAPI doesn't | CAPI token expired / wrong / has no permission | Regenerate in Events Manager, update Coolify, redeploy |
