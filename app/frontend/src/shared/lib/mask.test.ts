import { describe, expect, it } from "vitest";
import { captureText, maskForCapture } from "./mask";

describe("maskForCapture", () => {
  /** Emails are replaced wherever they appear in a sentence. */
  it("masks emails", () => {
    expect(maskForCapture("Write to a.b+c@example.co.uk today.")).toBe(
      "Write to [email] today.",
    );
  });

  /** International numbers with spaces, dashes, dots and brackets are masked. */
  it.each([
    "+20 100 555 0199",
    "+201005550199",
    "+1 (555) 010-0199",
    "+44.20.7946.0958",
    "+49-30-1234567",
  ])("masks the international number %s", (phone) => {
    expect(maskForCapture(`Call ${phone} now`)).toBe("Call [phone] now");
  });

  /** Local formats and bare digit runs of 10-15 digits are masked. */
  it.each([
    "0100 555 0199",
    "010-555-0199",
    "(010) 555 0199",
    "01005550199",
    "201005550199",
  ])("masks the local number %s", (phone) => {
    expect(maskForCapture(`Mobile: ${phone}.`)).toBe("Mobile: [phone].");
  });

  /** Secrets that could land in a message are masked. */
  it("masks key-shaped secrets", () => {
    expect(maskForCapture("key sk-canaryABCDEFGHIJKLMNOPQRS ok")).toBe(
      "key [secret] ok",
    );
  });

  /** SKUs, prices, quantities, dates and quote numbers are never touched. */
  it.each([
    "Quote 120 OD-001 and AB-123 at $32.35 each",
    "Total $1,234.56 for 3 units, 100 available",
    "Valid until 2026-11-05 or 03.11.2026 or 2026-11-03T08:00:00Z",
    "Reference LQ-418208D0, IP44, 4000K, 1800 lm",
    "Quantities 120 80 60 40 and 12345678",
    "Version 1.2.3 build 20261103",
  ])("leaves ordinary figures alone: %s", (text) => {
    expect(maskForCapture(text)).toBe(text);
  });

  /** Several values in one body are all masked and the rest of the text is kept. */
  it("masks several values in one message", () => {
    expect(
      maskForCapture(
        "Quote 120 OD-001. My number is +20 100 555 0199, mail me@x.io, key sk-canaryABCDEFGHIJKLMNOPQRS.",
      ),
    ).toBe(
      "Quote 120 OD-001. My number is [phone], mail [email], key [secret].",
    );
  });
});

describe("captureText", () => {
  /** Normal mode must show the real text, capture mode the masked text. */
  it("masks only in capture mode", () => {
    expect(captureText("me@x.io", false)).toBe("me@x.io");
    expect(captureText("me@x.io", true)).toBe("[email]");
  });
});
