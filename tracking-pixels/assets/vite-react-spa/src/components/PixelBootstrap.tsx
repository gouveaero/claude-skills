/**
 * Loads all enabled platform pixels for the Vite SPA.
 * Mount once at the top of your root component (App.tsx or main.tsx).
 *
 * Reads VITE_* env vars (Vite exposes only VITE_-prefixed vars to the client bundle).
 */

import { useEffect } from 'react';
import { captureAttributionCookies } from '../lib/cookies';
import { track } from '../lib/track';

const META_PIXEL_ID = import.meta.env.VITE_META_PIXEL_ID;
const GA4_MEASUREMENT_ID = import.meta.env.VITE_GA4_MEASUREMENT_ID;
const GOOGLE_ADS_CONVERSION_ID = import.meta.env.VITE_GOOGLE_ADS_CONVERSION_ID;
const TIKTOK_PIXEL_ID = import.meta.env.VITE_TIKTOK_PIXEL_ID;

function injectScript(id: string, content: string) {
  if (document.getElementById(id)) return;
  const s = document.createElement('script');
  s.id = id;
  s.async = true;
  s.text = content;
  document.head.appendChild(s);
}

function injectExternalScript(id: string, src: string) {
  if (document.getElementById(id)) return;
  const s = document.createElement('script');
  s.id = id;
  s.async = true;
  s.src = src;
  document.head.appendChild(s);
}

export function PixelBootstrap() {
  useEffect(() => {
    captureAttributionCookies();

    if (META_PIXEL_ID) {
      injectScript(
        'meta-pixel',
        `!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)};
        if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
        n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];
        s.parentNode.insertBefore(t,s)}(window,document,'script',
        'https://connect.facebook.net/en_US/fbevents.js');
        fbq('init', '${META_PIXEL_ID}');`,
      );
    }

    const gtagId = GA4_MEASUREMENT_ID ?? GOOGLE_ADS_CONVERSION_ID;
    if (gtagId) {
      injectExternalScript('gtag-loader', `https://www.googletagmanager.com/gtag/js?id=${gtagId}`);
      injectScript(
        'gtag-init',
        `window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        window.gtag = gtag;
        gtag('js', new Date());
        ${GA4_MEASUREMENT_ID ? `gtag('config', '${GA4_MEASUREMENT_ID}', { send_page_view: false });` : ''}
        ${GOOGLE_ADS_CONVERSION_ID ? `gtag('config', '${GOOGLE_ADS_CONVERSION_ID}', { allow_enhanced_conversions: true });` : ''}`,
      );
    }

    if (TIKTOK_PIXEL_ID) {
      injectScript(
        'tiktok-pixel',
        `!function (w, d, t) {
          w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];
          ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie"];
          ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};
          for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);
          ttq.instance=function(t){for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e};
          ttq.load=function(e,n){var i="https://analytics.tiktok.com/i18n/pixel/events.js";ttq._i=ttq._i||{};ttq._i[e]=[];ttq._i[e]._u=i;ttq._t=ttq._t||{};ttq._t[e]=+new Date;ttq._o=ttq._o||{};ttq._o[e]=n||{};var o=document.createElement("script");o.type="text/javascript";o.async=!0;o.src=i+"?sdkid="+e+"&lib="+t;var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(o,a)};
          ttq.load('${TIKTOK_PIXEL_ID}');
          ttq.page();
        }(window, document, 'ttq');`,
      );
    }

    void track('PageView');
  }, []);

  return null;
}
