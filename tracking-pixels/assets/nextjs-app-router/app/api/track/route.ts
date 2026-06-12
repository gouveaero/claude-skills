/**
 * Server-side fan-out endpoint.
 *
 * Receives the universal track() POST, enriches with server-only signals
 * (IP, UA, cookies), hashes PII, and fires to:
 *   - Meta Conversions API
 *   - GA4 Measurement Protocol
 *   - TikTok Events API
 *
 * Google Ads Enhanced Conversions for Web is handled CLIENT-SIDE via gtag
 * (it's not a server-side API for the on-site case).
 *
 * Returns 204 with X-Track-Status header summarizing each platform's status.
 */

import { NextResponse } from 'next/server';
import {
  sha256,
  normalizeEmail,
  normalizePhone,
  normalizeName,
  normalizeCity,
  normalizeState,
  normalizeZip,
  normalizeCountry,
  hashIfPresent,
} from '@/lib/hash';
import { readTrackingCookies } from '@/lib/cookies';

type TrackBody = {
  name: string;
  params: {
    value?: number;
    currency?: string;
    email?: string;
    phone?: string;
    firstName?: string;
    lastName?: string;
    externalId?: string;
    city?: string;
    state?: string;
    postalCode?: string;
    country?: string;
    contentIds?: string[];
    contentType?: string;
    contents?: Array<{ id: string; quantity?: number; price?: number; name?: string }>;
    searchString?: string;
  };
  event_id: string;
  event_time: number;
  event_source_url: string;
  ga4_client_id?: string;
  ga4_session_id?: string;
};

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

export async function POST(request: Request) {
  let body: TrackBody;
  try {
    body = await request.json();
  } catch {
    return new NextResponse('Invalid JSON', { status: 400 });
  }

  const cookies = readTrackingCookies(request.headers.get('cookie'));
  const ip =
    (request.headers.get('x-forwarded-for') ?? '').split(',')[0].trim() ||
    request.headers.get('x-real-ip') ||
    undefined;
  const ua = request.headers.get('user-agent') ?? undefined;

  const tasks: Array<Promise<{ platform: string; status: string }>> = [];

  if (process.env.META_PIXEL_ID && process.env.META_CAPI_TOKEN) {
    tasks.push(sendToMeta(body, cookies, ip, ua));
  }
  if (process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID && process.env.GA4_API_SECRET) {
    tasks.push(sendToGa4(body, ip, ua));
  }
  if (process.env.TIKTOK_PIXEL_ID && process.env.TIKTOK_ACCESS_TOKEN) {
    tasks.push(sendToTiktok(body, cookies, ip, ua));
  }

  const results = await Promise.allSettled(tasks);
  const statusHeader = results
    .map((r) =>
      r.status === 'fulfilled' ? `${r.value.platform}=${r.value.status}` : `unknown=rejected`,
    )
    .join(',');

  return new NextResponse(null, {
    status: 204,
    headers: { 'X-Track-Status': statusHeader || 'no_platforms_enabled' },
  });
}

async function sendToMeta(
  body: TrackBody,
  cookies: { _fbp?: string; _fbc?: string },
  ip?: string,
  ua?: string,
): Promise<{ platform: string; status: string }> {
  const pixelId = process.env.META_PIXEL_ID!;
  const token = process.env.META_CAPI_TOKEN!;
  const version = process.env.META_GRAPH_VERSION ?? 'v25.0';
  const testCode = process.env.META_TEST_EVENT_CODE;

  const p = body.params;
  const user_data: Record<string, unknown> = {
    em: hashIfPresent(p.email && normalizeEmail(p.email)),
    ph: hashIfPresent(p.phone && normalizePhone(p.phone, false)),
    fn: hashIfPresent(p.firstName && normalizeName(p.firstName)),
    ln: hashIfPresent(p.lastName && normalizeName(p.lastName)),
    ct: hashIfPresent(p.city && normalizeCity(p.city)),
    st: hashIfPresent(p.state && normalizeState(p.state)),
    zp: hashIfPresent(p.postalCode && normalizeZip(p.postalCode)),
    country: hashIfPresent(p.country && normalizeCountry(p.country)),
    external_id: p.externalId ? sha256(p.externalId) : undefined,
    fbp: cookies._fbp,
    fbc: cookies._fbc,
    client_ip_address: ip,
    client_user_agent: ua,
  };

  // Strip undefined for cleaner payload
  Object.keys(user_data).forEach((k) => user_data[k] === undefined && delete user_data[k]);

  const event = {
    event_name: META_NAME[body.name] ?? body.name,
    event_time: body.event_time,
    event_id: body.event_id,
    action_source: 'website',
    event_source_url: body.event_source_url,
    user_data,
    custom_data: {
      value: p.value,
      currency: p.currency,
      content_ids: p.contentIds,
      content_type: p.contentType,
      contents: p.contents,
      search_string: p.searchString,
    },
  };

  const url = `https://graph.facebook.com/${version}/${pixelId}/events?access_token=${token}`;
  const payload: Record<string, unknown> = {
    data: [event],
    partner_agent: 'tracking-pixels-skill-v1',
  };
  if (testCode) payload.test_event_code = testCode;

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

async function sendToGa4(
  body: TrackBody,
  ip?: string,
  ua?: string,
): Promise<{ platform: string; status: string }> {
  const measurementId = process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID!;
  const apiSecret = process.env.GA4_API_SECRET!;
  const region = process.env.GA4_REGION === 'eu' ? 'region1.' : '';

  const url = `https://${region}www.google-analytics.com/mp/collect?measurement_id=${measurementId}&api_secret=${apiSecret}`;

  // GA4 requires client_id. If the client didn't send one (e.g. gtag not loaded), generate
  // a synthetic one — events will be attributed to a new user but at least they land.
  const clientId =
    body.ga4_client_id ?? `${Math.floor(Math.random() * 1e10)}.${body.event_time}`;

  const p = body.params;
  const eventParams: Record<string, unknown> = {
    engagement_time_msec: 1,
    value: p.value,
    currency: p.currency,
    transaction_id: body.event_id,
    page_location: body.event_source_url,
    items: p.contents?.map((c) => ({
      item_id: c.id,
      item_name: c.name,
      price: c.price,
      quantity: c.quantity,
    })),
  };
  // Session stitching — MP events without session_id land session-less and break
  // session-scoped reports. MP requires a numeric string.
  if (body.ga4_session_id && /^\d+$/.test(body.ga4_session_id)) {
    eventParams.session_id = body.ga4_session_id;
  }
  if (process.env.DEBUG_GA4 === '1') eventParams.debug_mode = true;

  const payload = {
    client_id: clientId,
    user_id: p.externalId,
    timestamp_micros: body.event_time * 1_000_000,
    events: [
      {
        name: GA4_NAME[body.name] ?? body.name.toLowerCase(),
        params: eventParams,
      },
    ],
  };

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(ua ? { 'User-Agent': ua } : {}),
        ...(ip ? { 'X-Forwarded-For': ip } : {}),
      },
      body: JSON.stringify(payload),
    });
    return { platform: 'ga4', status: res.ok ? 'ok' : `err${res.status}` };
  } catch {
    return { platform: 'ga4', status: 'fetch_failed' };
  }
}

async function sendToTiktok(
  body: TrackBody,
  cookies: { _ttp?: string; _ttclid?: string },
  ip?: string,
  ua?: string,
): Promise<{ platform: string; status: string }> {
  const pixelId = process.env.TIKTOK_PIXEL_ID!;
  const token = process.env.TIKTOK_ACCESS_TOKEN!;
  const testCode = process.env.TIKTOK_TEST_EVENT_CODE;

  const p = body.params;
  const user: Record<string, unknown> = {
    email: hashIfPresent(p.email && normalizeEmail(p.email)),
    phone: hashIfPresent(p.phone && normalizePhone(p.phone, false)),
    first_name: hashIfPresent(p.firstName && normalizeName(p.firstName)),
    last_name: hashIfPresent(p.lastName && normalizeName(p.lastName)),
    city: hashIfPresent(p.city && normalizeCity(p.city)),
    state: hashIfPresent(p.state && normalizeState(p.state)),
    zip_code: hashIfPresent(p.postalCode && normalizeZip(p.postalCode)),
    country: hashIfPresent(p.country && normalizeCountry(p.country)),
    external_id: p.externalId ? sha256(p.externalId) : undefined,
    ttclid: cookies._ttclid,
    ttp: cookies._ttp,
    ip,
    user_agent: ua,
  };
  Object.keys(user).forEach((k) => user[k] === undefined && delete user[k]);

  const event = {
    event: TIKTOK_NAME[body.name] ?? body.name,
    event_time: body.event_time,
    event_id: body.event_id,
    user,
    page: { url: body.event_source_url },
    properties: {
      value: p.value,
      currency: p.currency,
      contents: p.contents?.map((c) => ({
        content_id: c.id,
        content_name: c.name,
        price: c.price,
        quantity: c.quantity,
        content_type: 'product',
      })),
      search_string: p.searchString,
    },
  };

  const payload: Record<string, unknown> = {
    event_source: 'web',
    event_source_id: pixelId,
    partner_name: 'tracking-pixels-skill-v1',
    data: [event],
  };
  if (testCode) payload.test_event_code = testCode;

  try {
    const res = await fetch('https://business-api.tiktok.com/open_api/v1.3/event/track/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Access-Token': token },
      body: JSON.stringify(payload),
    });
    return { platform: 'tiktok', status: res.ok ? 'ok' : `err${res.status}` };
  } catch {
    return { platform: 'tiktok', status: 'fetch_failed' };
  }
}
