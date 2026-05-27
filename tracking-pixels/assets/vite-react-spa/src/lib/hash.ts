/**
 * Client-side hash helpers (limited use — most hashing happens server-side in the sidecar).
 *
 * For the Vite SPA, this file is only used if you need to hash something in the browser
 * before sending it elsewhere. The /api/track POST sends raw values to the sidecar
 * which does the hashing.
 *
 * IMPORTANT: Web Crypto's `crypto.subtle.digest` is async and only works on HTTPS / localhost.
 */

export async function sha256(input: string): Promise<string> {
  const buf = new TextEncoder().encode(input);
  const hash = await crypto.subtle.digest('SHA-256', buf);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function normalizePhone(raw: string, withPlus = false, defaultCountryCode = '55'): string {
  const digits = raw.replace(/[^\d]/g, '');
  const withCountry =
    digits.length === 11 || digits.length === 10 ? `${defaultCountryCode}${digits}` : digits;
  return withPlus ? `+${withCountry}` : withCountry;
}
