/**
 * Tracking sidecar — separate Coolify app that proxies events to ad-platform APIs.
 *
 * Why a sidecar? Vite SPAs have no server runtime — there's no place to receive a
 * POST and call out to Meta/GA4/TikTok with secrets. The sidecar is a small Bun
 * (or Node) service that runs alongside the main site under a subdomain
 * (e.g. track.leticialang.exosmkt.com).
 *
 * Deploy:
 *   - Coolify project: same as the main site
 *   - Application name: <client_code>-tracking
 *   - Dockerfile: this folder's Dockerfile
 *   - Domain: track.<primary_domain>
 *   - Env vars: copy server-only secrets here (META_CAPI_TOKEN, GA4_API_SECRET, TIKTOK_ACCESS_TOKEN, CORS_ORIGIN)
 *
 * The main Vite SPA POSTs to VITE_TRACKING_ENDPOINT (set to https://track.<domain>/api/track).
 */

import { createHash } from 'node:crypto';

const PORT = Number(process.env.PORT ?? 3000);
const CORS_ORIGIN = process.env.CORS_ORIGIN ?? '*';

// ─── Hash helpers ────────────────────────────────────────────────────────────

const sha256 = (s: string) => createHash('sha256').update(s).digest('hex');
const normEmail = (s: string) => s.trim().toLowerCase();
const normPhone = (s: string, withPlus: boolean) => {
  const digits = s.replace(/[^\d]/g, '');
  const withCountry = digits.length <= 11 ? `55${digits}` : digits;
  return withPlus ? `+${withCountry}` : withCountry;
};
const normName = (s: string) =>
  s
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z]/g, '');
const hashIf = (v: string | undefined) => (v ? sha256(v) : undefined);

// ─── Cookie reader ───────────────────────────────────────────────────────────

function readCookies(cookieHeader: string | null) {
  const out: Record<string, string> = {};
  if (!cookieHeader) return out;
  cookieHeader.split(';').forEach((pair) => {
    const i = pair.indexOf('=');
    if (i < 0) return;
    const k = pair.slice(0, i).trim();
    const v = decodeURIComponent(pair.slice(i + 1).trim());
    if (['_fbp', '_fbc', '_ttp', '_ttclid', '_ga', '_gcl_aw'].includes(k)) out[k] = v;
  });
  return out;
}

// ─── Platform name maps (must mirror src/lib/track.ts) ───────────────────────

const META_NAME: Record<string, string> = {
  PageView: 'PageView',
  Lead: 'Lead',
  Purchase: 'Purchase',
  InitiateCheckout: 'InitiateCheckout',
  AddPaymentInfo: 'AddPaymentInfo',
  CompleteRegistration: 'CompleteRegistration',
  ViewContent: 'ViewContent',
  Contact: 'Contact',
  Schedule: 'Schedule',
  SubmitApplication: 'SubmitApplication',
  Search: 'Search',
  AddToCart: 'AddToCart',
};

const GA4_NAME: Record<string, string> = {
  PageView: 'page_view',
  Lead: 'generate_lead',
  Purchase: 'purchase',
  InitiateCheckout: 'begin_checkout',
  AddPaymentInfo: 'add_payment_info',
  CompleteRegistration: 'sign_up',
  ViewContent: 'view_item',
  Contact: 'contact',
  Schedule: 'schedule',
  SubmitApplication: 'submit_application',
  Search: 'search',
  AddToCart: 'add_to_cart',
};

const TIKTOK_NAME: Record<string, string> = {
  PageView: 'Browse',
  Lead: 'SubmitForm',
  Purchase: 'CompletePayment',
  InitiateCheckout: 'InitiateCheckout',
  AddPaymentInfo: 'AddPaymentInfo',
  CompleteRegistration: 'CompleteRegistration',
  ViewContent: 'ViewContent',
  Contact: 'Contact',
  Schedule: 'ClickButton',
  SubmitApplication: 'SubmitForm',
  Search: 'Search',
  AddToCart: 'AddToCart',
};

// ─── Fan-out functions ───────────────────────────────────────────────────────

type TrackBody = {
  name: string;
  params: Record<string, unknown>;
  event_id: string;
  event_time: number;
  event_source_url: string;
  ga4_client_id?: string;
};

async function sendToMeta(body: TrackBody, cookies: Record<string, string>, ip?: string, ua?: string) {
  if (!process.env.META_PIXEL_ID || !process.env.META_CAPI_TOKEN) return { platform: 'meta', status: 'disabled' };

  const p = body.params as Record<string, string | number | undefined>;
  const user_data: Record<string, unknown> = {
    em: hashIf(p.email ? normEmail(p.email as string) : undefined),
    ph: hashIf(p.phone ? normPhone(p.phone as string, false) : undefined),
    fn: hashIf(p.firstName ? normName(p.firstName as string) : undefined),
    ln: hashIf(p.lastName ? normName(p.lastName as string) : undefined),
    external_id: p.externalId ? sha256(p.externalId as string) : undefined,
    fbp: cookies._fbp,
    fbc: cookies._fbc,
    client_ip_address: ip,
    client_user_agent: ua,
  };
  Object.keys(user_data).forEach((k) => user_data[k] === undefined && delete user_data[k]);

  const event = {
    event_name: META_NAME[body.name] ?? body.name,
    event_time: body.event_time,
    event_id: body.event_id,
    action_source: 'website',
    event_source_url: body.event_source_url,
    user_data,
    custom_data: { value: p.value, currency: p.currency },
  };

  const version = process.env.META_GRAPH_VERSION ?? 'v24.0';
  const url = `https://graph.facebook.com/${version}/${process.env.META_PIXEL_ID}/events?access_token=${process.env.META_CAPI_TOKEN}`;
  const payload: Record<string, unknown> = { data: [event], partner_agent: 'tracking-pixels-skill-v1' };
  if (process.env.META_TEST_EVENT_CODE) payload.test_event_code = process.env.META_TEST_EVENT_CODE;

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return { platform: 'meta', status: res.ok ? 'ok' : `err${res.status}` };
  } catch {
    return { platform: 'meta', status: 'fetch_failed' };
  }
}

async function sendToGa4(body: TrackBody, ip?: string, ua?: string) {
  if (!process.env.GA4_MEASUREMENT_ID || !process.env.GA4_API_SECRET) return { platform: 'ga4', status: 'disabled' };

  const region = process.env.GA4_REGION === 'eu' ? 'region1.' : '';
  const url = `https://${region}www.google-analytics.com/mp/collect?measurement_id=${process.env.GA4_MEASUREMENT_ID}&api_secret=${process.env.GA4_API_SECRET}`;

  const clientId = body.ga4_client_id ?? `${Math.floor(Math.random() * 1e10)}.${body.event_time}`;

  const p = body.params as Record<string, string | number | undefined>;
  const eventParams: Record<string, unknown> = {
    engagement_time_msec: 1,
    value: p.value,
    currency: p.currency,
    transaction_id: body.event_id,
    page_location: body.event_source_url,
  };
  if (process.env.DEBUG_GA4 === '1') eventParams.debug_mode = true;

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(ua ? { 'User-Agent': ua } : {}),
        ...(ip ? { 'X-Forwarded-For': ip } : {}),
      },
      body: JSON.stringify({
        client_id: clientId,
        user_id: p.externalId,
        timestamp_micros: body.event_time * 1_000_000,
        events: [{ name: GA4_NAME[body.name] ?? body.name.toLowerCase(), params: eventParams }],
      }),
    });
    return { platform: 'ga4', status: res.ok ? 'ok' : `err${res.status}` };
  } catch {
    return { platform: 'ga4', status: 'fetch_failed' };
  }
}

async function sendToTiktok(body: TrackBody, cookies: Record<string, string>, ip?: string, ua?: string) {
  if (!process.env.TIKTOK_PIXEL_ID || !process.env.TIKTOK_ACCESS_TOKEN)
    return { platform: 'tiktok', status: 'disabled' };

  const p = body.params as Record<string, string | number | undefined>;
  const user: Record<string, unknown> = {
    email: hashIf(p.email ? normEmail(p.email as string) : undefined),
    phone: hashIf(p.phone ? normPhone(p.phone as string, false) : undefined),
    external_id: p.externalId ? sha256(p.externalId as string) : undefined,
    ttclid: cookies._ttclid,
    ttp: cookies._ttp,
    ip,
    user_agent: ua,
  };
  Object.keys(user).forEach((k) => user[k] === undefined && delete user[k]);

  const payload: Record<string, unknown> = {
    event_source: 'web',
    event_source_id: process.env.TIKTOK_PIXEL_ID,
    partner_name: 'tracking-pixels-skill-v1',
    data: [
      {
        event: TIKTOK_NAME[body.name] ?? body.name,
        event_time: body.event_time,
        event_id: body.event_id,
        user,
        page: { url: body.event_source_url },
        properties: { value: p.value, currency: p.currency },
      },
    ],
  };
  if (process.env.TIKTOK_TEST_EVENT_CODE) payload.test_event_code = process.env.TIKTOK_TEST_EVENT_CODE;

  try {
    const res = await fetch('https://business-api.tiktok.com/open_api/v1.3/event/track/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Access-Token': process.env.TIKTOK_ACCESS_TOKEN! },
      body: JSON.stringify(payload),
    });
    return { platform: 'tiktok', status: res.ok ? 'ok' : `err${res.status}` };
  } catch {
    return { platform: 'tiktok', status: 'fetch_failed' };
  }
}

// ─── HTTP server (Bun.serve or equivalent) ───────────────────────────────────

const corsHeaders = {
  'Access-Control-Allow-Origin': CORS_ORIGIN,
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Allow-Credentials': 'true',
};

Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    if (req.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    if (url.pathname === '/health') {
      return new Response('ok', { status: 200, headers: corsHeaders });
    }

    if (url.pathname !== '/api/track' || req.method !== 'POST') {
      return new Response('not found', { status: 404, headers: corsHeaders });
    }

    let body: TrackBody;
    try {
      body = (await req.json()) as TrackBody;
    } catch {
      return new Response('bad json', { status: 400, headers: corsHeaders });
    }

    const cookies = readCookies(req.headers.get('cookie'));
    const ip = (req.headers.get('x-forwarded-for') ?? '').split(',')[0].trim() || undefined;
    const ua = req.headers.get('user-agent') ?? undefined;

    const results = await Promise.allSettled([
      sendToMeta(body, cookies, ip, ua),
      sendToGa4(body, ip, ua),
      sendToTiktok(body, cookies, ip, ua),
    ]);

    const statusHeader = results
      .map((r) => (r.status === 'fulfilled' ? `${r.value.platform}=${r.value.status}` : 'unknown=rejected'))
      .join(',');

    return new Response(null, { status: 204, headers: { ...corsHeaders, 'X-Track-Status': statusHeader } });
  },
});

console.log(`tracking-sidecar listening on :${PORT}`);
