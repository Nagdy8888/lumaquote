/**
 * Reduce one decoded audio channel to `buckets` peak values.
 * Inputs: samples in the range -1..1 and the number of bars wanted (>= 1).
 * Output: exactly `buckets` numbers in 0..1, each the largest absolute sample in
 * that bucket's slice (never below 0 or above 1). When there are fewer samples than
 * buckets, samples repeat so every bucket reads at least one sample; an empty
 * channel yields all zeros. Pure: no DOM, no side effects.
 */
export function computePeaks(channel: Float32Array, buckets: number): number[] {
  const count = Math.max(1, Math.floor(buckets));
  const peaks: number[] = new Array<number>(count).fill(0);
  const length = channel.length;
  if (length === 0) return peaks;
  for (let bucket = 0; bucket < count; bucket += 1) {
    const start = Math.min(length - 1, Math.floor((bucket * length) / count));
    const end = Math.min(
      length,
      Math.max(start + 1, Math.floor(((bucket + 1) * length) / count)),
    );
    let peak = 0;
    for (let index = start; index < end; index += 1) {
      const value = Math.abs(channel[index]);
      if (value > peak) peak = value;
    }
    peaks[bucket] = Math.min(1, peak);
  }
  return peaks;
}

/**
 * Scale peaks so the loudest bar reaches 1, so a quiet recording is still readable.
 * Input: peaks in 0..1. Output: a new array in 0..1; all zeros stay zeros. Pure.
 */
export function normalizePeaks(peaks: number[]): number[] {
  const loudest = Math.max(0, ...peaks);
  return loudest === 0 ? peaks.map(() => 0) : peaks.map((p) => p / loudest);
}

/**
 * Format seconds as `m:ss` for the elapsed/total text.
 * Input: seconds (non-finite or negative values read as 0). Output: e.g. "1:05". Pure.
 */
export function formatClock(seconds: number): string {
  const whole =
    Number.isFinite(seconds) && seconds > 0 ? Math.floor(seconds) : 0;
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}
