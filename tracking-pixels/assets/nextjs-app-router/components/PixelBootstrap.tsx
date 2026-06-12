/**
 * Loads all enabled platform pixels in the browser + captures attribution cookies.
 * Mount once in app/layout.tsx, just above {children}.
 *
 * When consent.lgpd_mode === 'gated' (in .tracking.json), wrap this in the
 * ConsentBanner component so pixels only load after user accepts.
 */

'use client';

import Script from 'next/script';
import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { track as _track } from '@/lib/track';
import { captureAttributionCookies } from '@/lib/cookies';

const META_PIXEL_ID = process.env.NEXT_PUBLIC_META_PIXEL_ID;
const GA4_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID;
const GOOGLE_ADS_CONVERSION_ID = process.env.NEXT_PUBLIC_GOOGLE_ADS_CONVERSION_ID;
const TIKTOK_PIXEL_ID = process.env.NEXT_PUBLIC_TIKTOK_PIXEL_ID;

export function PixelBootstrap() {
  const pathname = usePathname();

  useEffect(() => {
    captureAttributionCookies();
  }, []);

  // PageView on initial load AND on every client-side route change —
  // the layout persists across App Router navigations, so without the
  // pathname dependency only the hard load would be tracked.
  useEffect(() => {
    void _track('PageView');
  }, [pathname]);

  return (
    <>
      {/* Meta Pixel */}
      {META_PIXEL_ID && (
        <Script id="meta-pixel" strategy="afterInteractive">
          {`
            !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)}(window, document,'script',
            'https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', '${META_PIXEL_ID}');
          `}
        </Script>
      )}

      {/* GA4 + Google Ads share gtag.js */}
      {(GA4_MEASUREMENT_ID || GOOGLE_ADS_CONVERSION_ID) && (
        <>
          <Script
            src={`https://www.googletagmanager.com/gtag/js?id=${GA4_MEASUREMENT_ID ?? GOOGLE_ADS_CONVERSION_ID}`}
            strategy="afterInteractive"
          />
          <Script id="gtag-init" strategy="afterInteractive">
            {`
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              window.gtag = gtag;
              gtag('js', new Date());
              ${GA4_MEASUREMENT_ID ? `gtag('config', '${GA4_MEASUREMENT_ID}', { send_page_view: false });` : ''}
              ${GOOGLE_ADS_CONVERSION_ID ? `gtag('config', '${GOOGLE_ADS_CONVERSION_ID}', { allow_enhanced_conversions: true });` : ''}
            `}
          </Script>
        </>
      )}

      {/* TikTok Pixel */}
      {TIKTOK_PIXEL_ID && (
        <Script id="tiktok-pixel" strategy="afterInteractive">
          {`
            !function (w, d, t) {
              w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];
              ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie"];
              ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};
              for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);
              ttq.instance=function(t){for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e};
              ttq.load=function(e,n){var i="https://analytics.tiktok.com/i18n/pixel/events.js";ttq._i=ttq._i||{};ttq._i[e]=[];ttq._i[e]._u=i;ttq._t=ttq._t||{};ttq._t[e]=+new Date;ttq._o=ttq._o||{};ttq._o[e]=n||{};var o=document.createElement("script");o.type="text/javascript";o.async=!0;o.src=i+"?sdkid="+e+"&lib="+t;var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(o,a)};
              ttq.load('${TIKTOK_PIXEL_ID}');
              ttq.page();
            }(window, document, 'ttq');
          `}
        </Script>
      )}
    </>
  );
}
