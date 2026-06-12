/**
 * Attribution cookie capture (client) + reading helpers (server).
 *
 * Client-side: call captureAttributionCookies() once on mount (PixelBootstrap does this).
 * Server-side: pass the request's Cookie header to readTrackingCookies().
 */

export type TrackingCookies = {
  _fbp?: string;
  _fbc?: string;
  _ttp?: string;
  _ttclid?: string;
  _ga?: string;
  _gcl_aw?: string;
};

// ─── Client ──────────────────────────────────────────────────────────────────

function getCookie(name: string): string | undefined {
  if (typeof document === 'undefined') return undefined;
  const value = document.cookie
    .split(';')
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${name}=`));
  return value ? decodeURIComponent(value.slice(name.length + 1)) : undefined;
}

function setCookie(name: string, value: string, days: number) {
  if (typeof document === 'undefined') return;
  const expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
  const host = window.location.hostname;
  // Strip leading "www." and set on the root for cross-subdomain sharing
  const rootDomain = host.replace(/^www\./, '');
  const domainAttr = host.includes('.') ? `; Domain=.${rootDomain}` : '';
  const secureAttr = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `${name}=${encodeURIComponent(value)}; Expires=${expires}; Path=/${domainAttr}; SameSite=Lax${secureAttr}`;
}

/** Read URL params on landing and persist _fbc / _ttclid if click IDs are present. */
export function captureAttributionCookies() {
  if (typeof window === 'undefined') return;
  const params = new URLSearchParams(window.location.search);

  const fbclid = params.get('fbclid');
  if (fbclid && !getCookie('_fbc')) {
    setCookie('_fbc', `fb.1.${Date.now()}.${fbclid}`, 90);
  }

  const ttclid = params.get('ttclid');
  if (ttclid && !getCookie('_ttclid')) {
    setCookie('_ttclid', ttclid, 90);
  }
}

/**
 * GA4 client_id — use the gtag getter instead of regex on _ga.
 * Google changed the _ga cookie format in May 2025; regex parsing breaks silently.
 */
export function getGa4ClientId(measurementId: string): Promise<string | undefined> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined' || !(window as Window & { gtag?: Gtag.Gtag }).gtag) {
      return resolve(undefined);
    }
    let resolved = false;
    const done = (v: string | undefined) => {
      if (!resolved) {
        resolved = true;
        resolve(v);
      }
    };
    (window as Window & { gtag: Gtag.Gtag }).gtag(
      'get',
      measurementId,
      'client_id',
      (id) => done(typeof id === 'string' ? id : undefined),
    );
    setTimeout(() => done(undefined), 500);
  });
}

/**
 * GA4 session_id — needed for Measurement Protocol session stitching.
 * Without it, MP events land session-less and break session-scoped reports.
 * Primary: gtag getter. Fallback: parse the _ga_<CONTAINER> cookie
 * (handles pre-May-2025 "GS1.1.<sid>." and current "GS2.1.s<sid>$" formats).
 * MP requires session_id to be a numeric string (^\d+$).
 */
export function getGa4SessionId(measurementId: string): Promise<string | undefined> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined' || !(window as Window & { gtag?: Gtag.Gtag }).gtag) {
      return resolve(sessionIdFromCookie(measurementId));
    }
    let resolved = false;
    const done = (v: string | undefined) => {
      if (!resolved) {
        resolved = true;
        resolve(v);
      }
    };
    (window as Window & { gtag: Gtag.Gtag }).gtag(
      'get',
      measurementId,
      'session_id',
      (id) => done(typeof id === 'string' || typeof id === 'number' ? String(id) : undefined),
    );
    setTimeout(() => done(sessionIdFromCookie(measurementId)), 500);
  });
}

function sessionIdFromCookie(measurementId: string): string | undefined {
  const raw = getCookie(`_ga_${measurementId.replace(/^G-/, '')}`);
  const m = raw?.match(/^GS\d\.\d\.s?(\d{9,11})/);
  return m?.[1];
}

// ─── Server ──────────────────────────────────────────────────────────────────

export function readTrackingCookies(cookieHeader: string | null): TrackingCookies {
  if (!cookieHeader) return {};
  const out: TrackingCookies = {};
  cookieHeader.split(';').forEach((pair) => {
    const idx = pair.indexOf('=');
    if (idx < 0) return;
    const k = pair.slice(0, idx).trim();
    const v = pair.slice(idx + 1).trim();
    if (
      k === '_fbp' ||
      k === '_fbc' ||
      k === '_ttp' ||
      k === '_ttclid' ||
      k === '_ga' ||
      k === '_gcl_aw'
    ) {
      out[k] = decodeURIComponent(v);
    }
  });
  return out;
}

/** Extract bare gclid from _gcl_aw cookie (format: "GCL.{ts}.{gclid}"). */
export function parseGclid(gclAw: string | undefined): string | undefined {
  if (!gclAw) return undefined;
  const parts = gclAw.split('.');
  return parts.length >= 3 ? parts.slice(2).join('.') : undefined;
}
