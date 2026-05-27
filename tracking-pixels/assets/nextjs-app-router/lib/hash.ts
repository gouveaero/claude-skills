/**
 * PII hashing + normalization for ad-platform Conversions APIs.
 *
 * Rules differ per platform:
 *   Meta   — phone WITHOUT '+' (E.164 digits only)
 *   Google — phone WITH '+' (E.164 with leading +)
 *   TikTok — phone WITHOUT '+' (E.164 digits only)
 *   GA4    — same as Google (when sending user_data)
 *
 * Hash everywhere: SHA-256, hex string, lowercase.
 * Always call normalize* BEFORE sha256().
 */

import { createHash } from 'node:crypto';

export function sha256(input: string): string {
  return createHash('sha256').update(input).digest('hex');
}

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

/**
 * Normalize phone to E.164 digits.
 * @param raw - phone number (may have +, spaces, dashes, parens)
 * @param withPlus - true for Google Ads, false for Meta/TikTok
 * @param defaultCountryCode - prepended if number starts as local format (e.g. "11999..." → "5511999...")
 */
export function normalizePhone(raw: string, withPlus = false, defaultCountryCode = '55'): string {
  const digits = raw.replace(/[^\d]/g, '');
  // If user typed just 11 digits (BR mobile), assume Brazil and prepend 55
  const withCountry =
    digits.length === 11 || digits.length === 10 ? `${defaultCountryCode}${digits}` : digits;
  return withPlus ? `+${withCountry}` : withCountry;
}

export function normalizeName(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // strip diacritics
    .replace(/[^a-z]/g, '');
}

export function normalizeCity(city: string): string {
  return city
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/\s+/g, '');
}

export function normalizeState(state: string): string {
  return state.trim().toLowerCase();
}

export function normalizeZip(zip: string): string {
  return zip.trim().toLowerCase();
}

export function normalizeCountry(country: string): string {
  return country.trim().toLowerCase().slice(0, 2);
}

export function normalizeDob(dob: string): string {
  // Accept YYYY-MM-DD or YYYYMMDD; output YYYYMMDD
  return dob.replace(/[^\d]/g, '').slice(0, 8);
}

export function normalizeGender(gender: string): string {
  const g = gender.trim().toLowerCase().charAt(0);
  return g === 'f' || g === 'm' ? g : '';
}

/** Hash if value is present; return undefined if empty/missing. */
export function hashIfPresent(value: string | undefined | null): string | undefined {
  return value && value.length > 0 ? sha256(value) : undefined;
}
