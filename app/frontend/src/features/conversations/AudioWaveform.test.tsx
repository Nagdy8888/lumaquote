import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AudioWaveform } from "./AudioWaveform";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("AudioWaveform", () => {
  /** Without AudioContext only the native player renders and nothing is fetched. */
  it("falls back to the native player when AudioContext is missing", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("AudioContext", undefined);
    const { container } = render(<AudioWaveform url="blob:test" />);
    expect(screen.getByLabelText("Voice note audio")).toBeInTheDocument();
    expect(container.querySelector(".waveform-body")).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  /** A decode failure leaves the native player in place and shows no bars. */
  it("shows only the player when decoding fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({ arrayBuffer: async () => new ArrayBuffer(4) }),
    );
    const close = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal(
      "AudioContext",
      class {
        /** Reject like a corrupt file. */
        decodeAudioData() {
          return Promise.reject(new Error("bad data"));
        }
        close = close;
      },
    );
    const { container } = render(<AudioWaveform url="blob:test" />);
    await waitFor(() => expect(close).toHaveBeenCalledTimes(1));
    expect(container.querySelector(".waveform-body")).toBeNull();
    expect(screen.getByLabelText("Voice note audio")).toBeInTheDocument();
  });

  /** A decoded note draws 64 hidden bars plus the time text, and closes the context once. */
  it("draws 64 bars and closes the AudioContext after decoding", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({ arrayBuffer: async () => new ArrayBuffer(4) }),
    );
    const close = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal(
      "AudioContext",
      class {
        /** Return one decoded channel with a ramp so bars differ. */
        decodeAudioData() {
          return Promise.resolve({
            getChannelData: () =>
              Float32Array.from({ length: 640 }, (_, i) => i / 640),
          });
        }
        close = close;
      },
    );
    const { container } = render(<AudioWaveform url="blob:test" />);
    await waitFor(() =>
      expect(container.querySelectorAll("rect")).toHaveLength(64),
    );
    expect(container.querySelector(".waveform-track")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
    expect(screen.getByText("0:00 / 0:00")).toBeInTheDocument();
    expect(close).toHaveBeenCalledTimes(1);
  });
});
