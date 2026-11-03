const SECRETS = [
  /\bsk-[A-Za-z0-9_-]{16,}/g,
  /\blsv2_[A-Za-z0-9_-]{16,}/g,
  /\bEAA[A-Za-z0-9]{20,}/g,
  /\beyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]{8,}/g,
];
const EMAIL = /[\w.+-]+@[\w-]+\.[\w.-]+/g;
// A run that starts like a phone number; `looksLikePhone` then decides, so SKUs, prices, quantities and dates survive.
const PHONE_CANDIDATE = /(?<![\w.+-])\+?\(?\d[\d ().-]{6,18}\d(?![\w-])/g;
const DATE = /^\d{4}-\d{2}-\d{2}$|^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$/;

/**
 * Decide whether a candidate digit run is a phone number.
 * Rules: with a leading "+" it needs 8-15 digits; a bare run of digits needs 10-15;
 * a run with spaces, dashes, dots or brackets and no "+" needs 9-15 digits in at least
 * three groups whose last group has three or more digits, and must not be a date.
 * Pure. Known limit: local numbers written in groups of two digits (for example
 * "01 23 45 67 89") are not recognised.
 */
function looksLikePhone(candidate: string): boolean {
  const digits = candidate.replace(/\D/g, "").length;
  if (candidate.startsWith("+")) return digits >= 8 && digits <= 15;
  if (/^\d+$/.test(candidate)) return digits >= 10 && digits <= 15;
  if (digits < 9 || digits > 15 || DATE.test(candidate)) return false;
  const groups = candidate.split(/\D+/).filter(Boolean);
  return groups.length >= 3 && groups[groups.length - 1].length >= 3;
}

/**
 * Replace personal and secret-looking values in free text for screen captures.
 * Input: any text (a message body, a delivery preview). Output: the text with secrets
 * (`sk-`, `lsv2_`, `EAA` and bearer-JWT shapes) as "[secret]", emails as "[email]" and
 * phone numbers as "[phone]". It leaves SKUs (`AB-123`), prices, quantities, dates and
 * quote numbers alone. The patterns follow `PRIVATE` in the browser review scripts so the
 * review and the mask agree. Pure and display-only: it never changes stored data, and it
 * is applied only when capture mode is on. It is a best-effort pattern mask, not a
 * guarantee: names, addresses and numbers written in words are not detected.
 */
export function maskForCapture(text: string): string {
  let masked = text;
  for (const pattern of SECRETS) masked = masked.replace(pattern, "[secret]");
  masked = masked.replace(EMAIL, "[email]");
  return masked.replace(PHONE_CANDIDATE, (candidate) =>
    looksLikePhone(candidate) ? "[phone]" : candidate,
  );
}

/**
 * Show real text in normal mode and the masked text in capture mode.
 * Inputs: text and the capture flag. Output: `text` unchanged when `capture` is false.
 */
export function captureText(text: string, capture: boolean): string {
  return capture ? maskForCapture(text) : text;
}
