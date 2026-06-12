/**
 * Universal Event Layer — single client-side API that fans out to:
 *   - Meta Pixel (fbq) + Conversions API (via /api/track → CAPI)
 *   - Google Ads gtag conversion + Enhanced Conversions for Web
 *   - GA4 gtag event + Measurement Protocol (via /api/track → MP)
 *   - TikTok Pixel (ttq) + Events API (via /api/track → TikTok)
 *
 * The same event_id is used everywhere → dedup on Meta and TikTok (48h window),
 * and as transaction_id on GA4 / Google Ads for purchase-class dedup.
 *
 * Read references/universal-event-layer.md for the contract.
 */

import { getGa4ClientId } from './cookies';

export type EventName =
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

export type EventParams = {
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
};

const META_NAME: Record<EventName, string> = {
  PageView: 'PageView',
  ViewContent: 'ViewContent',
  Lead: 'Lead',
  CompleteRegistration: 'CompleteRegistration',
  InitiateCheckout: 'InitiateCheckout',
  AddPaymentInfo: 'AddPaymentInfo',
  Purchase: 'Purchase',
  Contact: 'Contact',
  Schedule: 'Schedule',
  SubmitApplication: 'SubmitApplication',
  Search: 'Search',
  AddToCart: 'AddToCart',
};

const GA4_NAME: Record<EventName, string> = {
  PageView: 'page_view',
  ViewContent: 'view_item',
  Lead: 'generate_lead',
  CompleteRegistration: 'sign_up',
  InitiateCheckout: 'begin_checkout',
  AddPaymentInfo: 'add_payment_info',
  Purchase: 'purchase',
  Contact: 'contact',
  Schedule: 'schedule',
  SubmitApplication: 'submit_application',
  Search: 'search',
  AddToCart: 'add_to_cart',
};

const TIKTOK_NAME: Record<EventName, string> = {
  PageView: 'Browse',
  ViewContent: 'ViewContent',
  Lead: 'SubmitForm',
  CompleteRegistration: 'CompleteRegistration',
  InitiateCheckout: 'InitiateCheckout',
  AddPaymentInfo: 'AddPaymentInfo',
  Purchase: 'CompletePayment',
  Contact: 'Contact',
  Schedule: 'ClickButton',
  SubmitApplication: 'SubmitForm',
  Search: 'Search',
  AddToCart: 'AddToCart',
};

declare global {
  interface Window {
    fbq?: (...args: unknown[]) => void;
    ttq?: {
      track: (name: string, props?: Record<string, unknown>, opts?: { event_id?: string }) => void;
      page: () => void;
    };
  }
}

function toMetaProps(p: EventParams): Record<string, unknown> {
  return {
    value: p.value,
    currency: p.currency,
    content_ids: p.contentIds,
    content_type: p.contentType,
    contents: p.contents,
    search_string: p.searchString,
  };
}

function toGtagProps(p: EventParams): Record<string, unknown> {
  return {
    value: p.value,
    currency: p.currency,
    items: p.contents?.map((c) => ({
      item_id: c.id,
      item_name: c.name,
      price: c.price,
      quantity: c.quantity,
    })),
    search_term: p.searchString,
  };
}

function toTiktokProps(p: EventParams): Record<string, unknown> {
  return {
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
  };
}

export async function track(name: EventName, params: EventParams = {}): Promise<void> {
  const event_id =
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const event_time = Math.floor(Date.now() / 1000);
  const event_source_url = typeof location !== 'undefined' ? location.href : '';

  // 1. Client-side fan-out — fires Pixel/ttq/gtag with the SAME event_id
  if (typeof window !== 'undefined') {
    window.fbq?.('track', META_NAME[name], toMetaProps(params), { eventID: event_id });
    window.ttq?.track(TIKTOK_NAME[name], toTiktokProps(params), { event_id });

    const gtag = (window as Window & { gtag?: Gtag.Gtag }).gtag;
    if (gtag) {
      // GA4 event
      gtag('event', GA4_NAME[name], {
        ...toGtagProps(params),
        transaction_id: event_id,
        engagement_time_msec: 1,
      });

      // Google Ads conversion (if conversion_id + label configured for this event)
      const conversionId = process.env.NEXT_PUBLIC_GOOGLE_ADS_CONVERSION_ID;
      const labelEnvKey = `NEXT_PUBLIC_GADS_LABEL_${name.toUpperCase()}`;
      const label = process.env[labelEnvKey];
      if (conversionId && label) {
        // Set user_data BEFORE the conversion (Enhanced Conversions)
        gtag('set', 'user_data', {
          email: params.email,
          phone_number: params.phone ? ensurePlus(params.phone) : undefined,
          address: {
            first_name: params.firstName,
            last_name: params.lastName,
            postal_code: params.postalCode,
            country: params.country,
          },
        });
        gtag('event', 'conversion', {
          send_to: `${conversionId}/${label}`,
          value: params.value,
          currency: params.currency ?? 'BRL',
          transaction_id: event_id,
        });
      }
    }
  }

  // 2. Server-side fan-out — POST raw params (server hashes PII once)
  const ga4ClientId =
    process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID && typeof window !== 'undefined'
      ? await getGa4ClientId(process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID)
      : undefined;

  const endpoint = process.env.NEXT_PUBLIC_TRACKING_ENDPOINT || '/api/track/';

  try {
    await fetch(endpoint, {
      method: 'POST',
      keepalive: true, // survive navigation
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        params,
        event_id,
        event_time,
        event_source_url,
        ga4_client_id: ga4ClientId,
      }),
    });
  } catch {
    // Silent fail — never block UX on tracking
  }
}

function ensurePlus(phone: string): string {
  return phone.startsWith('+') ? phone : `+${phone.replace(/[^\d]/g, '')}`;
}
