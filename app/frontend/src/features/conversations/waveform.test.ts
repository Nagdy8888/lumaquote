import { describe, expect, it } from "vitest";
import { computePeaks, formatClock, normalizePeaks } from "./waveform";

describe("computePeaks", () => {
  /** Silence yields the requested number of zero peaks. */
  it("returns zeros for silence", () => {
    expect(computePeaks(new Float32Array(1000), 64)).toEqual(
      new Array(64).fill(0),
    );
  });

  /** A single spike appears only in its own bucket, as an absolute value. */
  it("puts a single spike in one bucket", () => {
    const channel = new Float32Array(640);
    channel[330] = -0.5;
    const peaks = computePeaks(channel, 64);
    expect(peaks).toHaveLength(64);
    expect(peaks[33]).toBeCloseTo(0.5);
    expect(peaks.filter((p) => p > 0)).toHaveLength(1);
  });

  /** Fewer samples than buckets still returns every bucket, repeating samples. */
  it("handles fewer samples than buckets", () => {
    const peaks = computePeaks(Float32Array.from([0.2, -0.8, 0.4]), 8);
    expect(peaks).toHaveLength(8);
    expect(Math.max(...peaks)).toBeCloseTo(0.8);
    expect(Math.min(...peaks)).toBeGreaterThanOrEqual(0);
  });

  /** An empty channel and out-of-range samples stay inside 0..1. */
  it("clamps to 0..1 and tolerates an empty channel", () => {
    expect(computePeaks(new Float32Array(0), 4)).toEqual([0, 0, 0, 0]);
    expect(computePeaks(Float32Array.from([3, -4]), 2)).toEqual([1, 1]);
  });
});

describe("normalizePeaks", () => {
  /** The loudest bar becomes 1 and silence stays silent. */
  it("scales to the loudest bar", () => {
    expect(normalizePeaks([0.1, 0.2, 0.05])).toEqual([0.5, 1, 0.25]);
    expect(normalizePeaks([0, 0])).toEqual([0, 0]);
  });
});

describe("formatClock", () => {
  /** Seconds become m:ss and bad input reads as 0:00. */
  it("formats minutes and seconds", () => {
    expect(formatClock(65.9)).toBe("1:05");
    expect(formatClock(0)).toBe("0:00");
    expect(formatClock(Number.NaN)).toBe("0:00");
    expect(formatClock(Infinity)).toBe("0:00");
  });
});
