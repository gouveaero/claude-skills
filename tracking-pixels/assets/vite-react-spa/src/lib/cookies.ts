/**
 * Client-side cookie capture for Vite SPA.
 * The sidecar (separate service) does the server-side reading.
 */

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
  const rootDomain = host.replace(/^www\./, '');
  const domainAttr = host.includes('.') ? `; Domain=.${rootDomain}` : '';
  const secureAttr = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `${name}=${encodeURIComponent(value)}; Expires=${expires}; Path=/${domainAttr}; SameSite=Lax${secureAttr}`;
}

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

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

export function getGa4ClientId(measurementId: string): Promise<string | undefined> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined' || !window.gtag) return resolve(undefined);
    let resolved = false;
    const done = (v: string | undefined) => {
      if (!resolved) {
        resolved = true;
        resolve(v);
      }
    };
    window.gtag('get', measurementId, 'client_id', (id: string) => done(id));
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
    if (typeof window === 'undefined' || !window.gtag) {
      return resolve(sessionIdFromCookie(measurementId));
    }
    let resolved = false;
    const done = (v: string | undefined) => {
      if (!resolved) {
        resolved = true;
        resolve(v);
      }
    };
    window.gtag('get', measurementId, 'session_id', (id: unknown) =>
      done(typeof id === 'string' || typeof id === 'number' ? String(id) : undefined),
    );
    setTimeout(() => done(sessionIdFromCookie(measurementId)), 500);
  });
}

function sessionIdFromCookie(measurementId: string): string | undefined {
  const raw = getCookie(`_ga_${measurementId.replace(/^G-/, '')}`);
  const m = raw?.match(/^GS\d\.\d\.s?(\d{9,11})/);
  return m?.[1];
}
