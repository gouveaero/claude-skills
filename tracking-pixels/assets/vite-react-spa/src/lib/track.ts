/**
 * Universal Event Layer for Vite SPA.
 *
 * Same contract as the Next.js template, but POSTs to the sidecar service
 * (e.g. https://track.leticialang.exosmkt.com/api/track) instead of a local
 * route handler.
 */

import { getGa4ClientId, getGa4SessionId } from './cookies';

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

const TRACKING_ENDPOINT = import.meta.env.VITE_TRACKING_ENDPOINT;
const GA4_ID = import.meta.env.VITE_GA4_MEASUREMENT_ID;
const GADS_ID = import.meta.env.VITE_GOOGLE_ADS_CONVERSION_ID;

export async function track(name: EventName, params: EventParams = {}): Promise<void> {
  const event_id =
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const event_time = Math.floor(Date.now() / 1000);
  const event_source_url = typeof location !== 'undefined' ? location.href : '';

  if (typeof window !== 'undefined') {
    window.fbq?.(
      'track',
      META_NAME[name],
      { value: params.value, currency: params.currency },
      { eventID: event_id },
    );
    window.ttq?.track(
      TIKTOK_NAME[name],
      { value: params.value, currency: params.currency },
      { event_id },
    );

    if (window.gtag) {
      window.gtag('event', GA4_NAME[name], {
        value: params.value,
        currency: params.currency,
        transaction_id: event_id,
        engagement_time_msec: 1,
      });

      const labelKey = `VITE_GADS_LABEL_${name.toUpperCase()}`;
      const label = (import.meta.env as Record<string, string | undefined>)[labelKey];
      if (GADS_ID && label) {
        window.gtag('set', 'user_data', {
          email: params.email,
          phone_number: params.phone ? ensurePlus(params.phone) : undefined,
          address: {
            first_name: params.firstName,
            last_name: params.lastName,
            postal_code: params.postalCode,
            country: params.country,
          },
        });
        window.gtag('event', 'conversion', {
          send_to: `${GADS_ID}/${label}`,
          value: params.value,
          currency: params.currency ?? 'BRL',
          transaction_id: event_id,
        });
      }
    }
  }

  const [ga4ClientId, ga4SessionId] =
    GA4_ID && typeof window !== 'undefined'
      ? await Promise.all([getGa4ClientId(GA4_ID), getGa4SessionId(GA4_ID)])
      : [undefined, undefined];

  if (!TRACKING_ENDPOINT) return;

  try {
    await fetch(TRACKING_ENDPOINT, {
      method: 'POST',
      keepalive: true,
      mode: 'cors',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        name,
        params,
        event_id,
        event_time,
        event_source_url,
        ga4_client_id: ga4ClientId,
        ga4_session_id: ga4SessionId,
      }),
    });
  } catch {
    /* silent */
  }
}

function ensurePlus(phone: string): string {
  return phone.startsWith('+') ? phone : `+${phone.replace(/[^\d]/g, '')}`;
}
