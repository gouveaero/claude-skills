/**
 * LGPD/GDPR consent banner — opt-in mode only.
 *
 * Activated by switching .tracking.json `consent.lgpd_mode` to "gated".
 * Mount inside <PixelBootstrap /> so pixels gate on consent state.
 *
 * Reads/writes cookie `consent-state` = 'granted' | 'denied' | 'pending'.
 * Cookie has 365-day expiry; user can revoke via a small "Cookies" link in the footer
 * (the integrator wires that up — this component just exposes window.__revokeConsent).
 *
 * Visual style is minimal Tailwind — restyle to match the brand. The skill notes this
 * in the post-install checklist for `enable-lgpd` mode.
 */

'use client'; // remove this line if using Vite — it's a Next.js directive

import { useEffect, useState } from 'react';

type ConsentState = 'pending' | 'granted' | 'denied';

const COOKIE_NAME = 'consent-state';
const COOKIE_DAYS = 365;

function readCookie(name: string): string | undefined {
  if (typeof document === 'undefined') return undefined;
  const v = document.cookie
    .split(';')
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${name}=`));
  return v ? decodeURIComponent(v.slice(name.length + 1)) : undefined;
}

function writeCookie(name: string, value: string, days: number) {
  const expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
  const host = window.location.hostname;
  const rootDomain = host.replace(/^www\./, '');
  const domainAttr = host.includes('.') ? `; Domain=.${rootDomain}` : '';
  const secureAttr = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `${name}=${encodeURIComponent(value)}; Expires=${expires}; Path=/${domainAttr}; SameSite=Lax${secureAttr}`;
}

export function ConsentBanner({
  onGrant,
  onDeny,
}: {
  onGrant: () => void;
  onDeny: () => void;
}) {
  const [state, setState] = useState<ConsentState>('pending');

  useEffect(() => {
    const stored = readCookie(COOKIE_NAME) as ConsentState | undefined;
    if (stored === 'granted' || stored === 'denied') {
      setState(stored);
      stored === 'granted' ? onGrant() : onDeny();
    }
    // Expose a way for a footer link to re-open the banner
    (window as Window & { __revokeConsent?: () => void }).__revokeConsent = () => {
      writeCookie(COOKIE_NAME, 'pending', 1);
      setState('pending');
    };
  }, [onGrant, onDeny]);

  if (state !== 'pending') return null;

  const grant = () => {
    writeCookie(COOKIE_NAME, 'granted', COOKIE_DAYS);
    setState('granted');
    onGrant();
    // Notify Meta Pixel + TikTok Pixel if they were loaded in revoked mode
    (window as Window & { fbq?: (...args: unknown[]) => void }).fbq?.('consent', 'grant');
    const ttq = (window as Window & { ttq?: { enableCookie?: () => void } }).ttq;
    ttq?.enableCookie?.();
    // GA4 Consent Mode v2 update
    (window as Window & { gtag?: (...args: unknown[]) => void }).gtag?.('consent', 'update', {
      ad_storage: 'granted',
      analytics_storage: 'granted',
      ad_user_data: 'granted',
      ad_personalization: 'granted',
    });
  };

  const deny = () => {
    writeCookie(COOKIE_NAME, 'denied', COOKIE_DAYS);
    setState('denied');
    onDeny();
  };

  return (
    <div
      role="dialog"
      aria-label="Aviso de privacidade"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        padding: '16px',
        background: 'rgba(20, 20, 20, 0.96)',
        color: '#fff',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        fontSize: '14px',
        lineHeight: 1.4,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
        boxShadow: '0 -4px 12px rgba(0,0,0,0.2)',
      }}
    >
      <p style={{ flex: '1 1 320px', margin: 0 }}>
        Usamos cookies para medir o desempenho deste site e personalizar conteúdo. Você pode aceitar
        todos ou recusar os não-essenciais.{' '}
        <a href="/privacidade" style={{ color: '#80b3ff', textDecoration: 'underline' }}>
          Saiba mais
        </a>
        .
      </p>
      <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
        <button
          onClick={deny}
          style={{
            padding: '8px 16px',
            background: 'transparent',
            color: '#fff',
            border: '1px solid rgba(255,255,255,0.4)',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Recusar
        </button>
        <button
          onClick={grant}
          style={{
            padding: '8px 16px',
            background: '#fff',
            color: '#000',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '14px',
          }}
        >
          Aceitar todos
        </button>
      </div>
    </div>
  );
}
