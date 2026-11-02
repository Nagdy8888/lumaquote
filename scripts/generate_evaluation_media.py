"""Generate the synthetic voice and label-photo assets that the 80-scenario set declares.

Voice: Windows System.Speech (David/Zira, en-US) renders each scripted utterance,
then deterministic degradations are applied from the scenario's declared
conditions (noise, telephone band, clipping, overlapping speaker, speaking rate).
Photos: Pillow renders labels, specification plates, cartons and scene photos with
declared defects (glare, sticker, blur, fading, handwriting, strike-through).

This is synthetic text-to-speech and drawn imagery. It is more demanding than clean
studio audio but is NOT human speech or a camera capture, and its results must not
be reported as such. Output is deterministic per scenario/turn id. The script
rewrites each media turn's `spec.asset` in `scenarios.json`, writes
`media/MANIFEST.json` (hashes and generation parameters, never expected outcomes)
and never reads the answer key.
"""

import array
import audioop
import hashlib
import json
import math
import random
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import evaluation_dataset as dataset
from PIL import Image, ImageDraw, ImageFilter, ImageFont

MEDIA = dataset.FIXTURES / "media"
RATE = 16000
SKU = re.compile(r"\b([A-Z])([A-Z])-(\d)(\d)(\d)\b")
DIGITS = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}
FONTS = Path("C:/Windows/Fonts")

POWERSHELL = r"""
Add-Type -AssemblyName System.Speech
$items = Get-Content -Raw -Encoding UTF8 $args[0] | ConvertFrom-Json
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
foreach ($item in $items) {
  $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $s.SelectVoice($item.voice)
  $s.Rate = [int]$item.rate
  $s.SetOutputToWaveFile($item.path, $fmt)
  $s.Speak($item.text)
  $s.Dispose()
}
"""


def spoken(text: str) -> str:
    """Spell catalog codes the way a person would say them so synthesis does not read 'DL-006' as a word."""
    return SKU.sub(lambda m: f"{m[1]} {m[2]} dash " + " ".join(DIGITS[d] for d in m.groups()[2:]), text)


def synthesize(jobs: list[dict]) -> None:
    """Render every queued utterance with System.Speech in one PowerShell process (Windows only)."""
    with tempfile.TemporaryDirectory() as folder:
        manifest, script = Path(folder) / "jobs.json", Path(folder) / "speak.ps1"
        manifest.write_text(json.dumps(jobs), encoding="utf-8")
        script.write_text(POWERSHELL, encoding="utf-8")
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), str(manifest)],
            check=True,
            capture_output=True,
            timeout=600,
        )


def read_wave(path: Path) -> bytes:
    """Return 16 kHz mono 16-bit PCM frames from a synthesized file."""
    with wave.open(str(path), "rb") as source:
        assert (source.getframerate(), source.getnchannels(), source.getsampwidth()) == (RATE, 1, 2)
        return source.readframes(source.getnframes())


def mix(base: bytes, other: bytes, offset: int = 0, gain: float = 1.0) -> bytes:
    """Add `other` (scaled) to `base` starting at a sample offset, extending the result when needed."""
    other = audioop.mul(other, 2, gain)
    pad = b"\0\0" * offset
    other = pad + other
    length = max(len(base), len(other))
    return audioop.add(base.ljust(length, b"\0"), other.ljust(length, b"\0"), 2)


def noise(frames: int, rng: random.Random, amplitude: int) -> bytes:
    """Create broadband noise with a low-frequency hum, as from a workshop or vehicle."""
    samples = array.array("h")
    for n in range(frames):
        hum = int(amplitude * 0.5 * math.sin(2 * math.pi * 90 * n / RATE))
        samples.append(max(-32768, min(32767, rng.randint(-amplitude, amplitude) + hum)))
    return samples.tobytes()


def degrade(
    frames: bytes, conditions: list[str], rng: random.Random, second: bytes | None
) -> tuple[bytes, list[str]]:
    """Apply deterministic degradations implied by the declared conditions; return audio and the steps used."""
    text, steps = " ".join(conditions).lower(), []
    if "overlap" in text and second:
        frames = mix(frames, second, offset=int(RATE * 0.9), gain=1.1)
        steps.append("overlapping second speaker")
    if "telephone" in text:
        narrow, _ = audioop.ratecv(frames, 2, 1, RATE, 8000, None)
        narrow = audioop.mul(narrow, 2, 0.8)
        frames, _ = audioop.ratecv(narrow, 2, 1, 8000, RATE, None)
        frames = mix(frames, noise(len(frames) // 2, rng, 350))
        steps.append("8 kHz telephone band with line noise")
    if "noise" in text or "signal-to-noise" in text:
        peak = max(1, audioop.max(frames, 2))
        ratio = 0.25 if "moderate" in text else 0.9
        frames = mix(frames, noise(len(frames) // 2, rng, int(peak * ratio)))
        steps.append(f"background noise at {ratio} of the speech peak with 90 Hz hum")
    if "clipped" in text:
        frames = audioop.mul(frames, 2, 8)
        samples = array.array("h", frames)
        limit = 9000
        frames = array.array("h", (max(-limit, min(limit, s)) for s in samples)).tobytes()
        steps.append("overdriven and hard clipped")
    return frames, steps


def write_wave(path: Path, frames: bytes) -> None:
    """Write 16 kHz mono 16-bit PCM."""
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(RATE)
        target.writeframes(frames)


def make_voice(items: list[tuple[str, dict]], manifest: dict) -> None:
    """Render and degrade every audio turn; `items` pairs a stem with its turn."""
    work = Path(tempfile.mkdtemp())
    jobs = []
    for stem, turn in items:
        rng = random.Random(stem)
        spec = turn["spec"]
        text = re.sub(r"\[[^\]]*\]", "", spec["utterance"])
        text = re.sub(r"\s{2,}", " ", text)
        conditions = " ".join(spec["conditions"]).lower()
        voice = rng.choice(["Microsoft David Desktop", "Microsoft Zira Desktop"])
        rate = 3 if "fast" in conditions else rng.choice([-1, 0, 0, 1])
        jobs.append({"voice": voice, "rate": rate, "text": spoken(text), "path": str(work / f"{stem}.wav")})
        if "overlap" in conditions:
            other = (
                "Microsoft Zira Desktop"
                if voice.endswith("Desktop") and "David" in voice
                else "Microsoft David Desktop"
            )
            jobs.append(
                {
                    "voice": other,
                    "rate": 1,
                    "text": "Sorry, which lights did you mean?",
                    "path": str(work / f"{stem}-b.wav"),
                }
            )
    synthesize(jobs)
    MEDIA.mkdir(parents=True, exist_ok=True)
    for stem, turn in items:
        rng = random.Random(stem + "-fx")
        base = read_wave(work / f"{stem}.wav")
        second = read_wave(work / f"{stem}-b.wav") if (work / f"{stem}-b.wav").exists() else None
        frames, steps = degrade(base, turn["spec"]["conditions"], rng, second)
        frames = b"\0\0" * int(RATE * 0.4) + frames + b"\0\0" * int(RATE * 0.4)
        name = f"{stem}.wav"
        write_wave(MEDIA / name, frames)
        manifest[name] = {
            "kind": "audio",
            "seconds": round(len(frames) / 2 / RATE, 2),
            "voice": next(j["voice"] for j in jobs if j["path"].endswith(f"{stem}.wav")),
            "degradations": steps or ["none (clean synthetic speech)"],
        }


def font(name: str, size: int):
    """Load a Windows font or fall back to Pillow's default so generation never silently changes layout."""
    return ImageFont.truetype(str(FONTS / name), size)


def sticker_text(label: str) -> list[str]:
    """Split label text into printed lines; parenthetical descriptors of the scene are not printed."""
    label = re.sub(r"^Spec plate:\s*", "", label)
    label = re.sub(r"\((?:handwritten|crossed out|old stock label|two stickers)\)", "", label)
    parts = [p.strip() for p in re.split(r"\s\|\s|\s/\s", label) if p.strip()]
    return parts


def draw_label(
    draw: ImageDraw.ImageDraw, box: tuple, lines: list[str], ink: str, handwriting: bool, struck_first: bool
) -> None:
    """Draw bordered text lines inside `box`; a '?' is left unprinted and covered by a sticker patch."""
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline=ink, width=4)
    size = max(28, min(80, (y1 - y0) // (len(lines) + 1)))
    face = (
        font("Inkfree.ttf", size + 6)
        if handwriting
        else font("bahnschrift.ttf" if len(lines) > 1 else "arial.ttf", size)
    )
    y = y0 + 18
    for index, line in enumerate(lines):
        printed = line.replace("?", " ")
        draw.text((x0 + 24, y), printed, fill=ink, font=face)
        if "?" in line:
            left = x0 + 24 + face.getlength(line[: line.index("?")])
            width = face.getlength("0") + 10
            draw.rectangle((left - 4, y - 6, left + width, y + size + 8), fill="#bdbdbd")
        left, top, right, bottom = draw.textbbox((x0 + 24, y), printed, font=face)
        if struck_first and index == 0:
            draw.line(
                (left - 6, (top + bottom) // 2, right + 6, (top + bottom) // 2), fill="#b00020", width=6
            )
        y += size + 18


def make_photo(stem: str, turn: dict, manifest: dict) -> None:
    """Render one label/plate/carton/scene image and apply the defects its conditions declare."""
    rng = random.Random(stem)
    spec = turn["spec"]
    conditions = " ".join(spec["conditions"]).lower()
    label = spec["label_text"]
    width, height = 960, 640
    background = rng.choice(["#d8d8d8", "#c9c2b0", "#9aa3a8"])
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    steps = []
    if "scene photo" in conditions:
        for gx in range(0, width, 160):
            draw.line((gx, 0, gx, height), fill="#aaaaaa", width=3)
        for gy in range(0, height, 160):
            draw.line((0, gy, width, gy), fill="#aaaaaa", width=3)
        draw.rectangle((380, 250, 580, 330), fill="#fffbe0", outline="#888888", width=4)
        steps.append("ceiling tiles and a luminaire, no printed text")
    else:
        plate = "specification plate" in conditions
        paper = "#8f9aa0" if plate else rng.choice(["#ffffff", "#fffde7", "#f4f4f4"])
        ink = "#101010"
        if "two labels" in conditions:
            lines = sticker_text(label)
            for index, line in enumerate(lines[:2]):
                x0 = 40 + index * 450
                draw.rectangle((x0, 180, x0 + 420, 420), fill=paper)
                draw_label(draw, (x0, 180, x0 + 420, 420), [line], ink, False, False)
            steps.append("two labels in one frame")
        else:
            lines = sticker_text(label)
            handwriting = "handwritten" in conditions and "correction" not in conditions
            if "correction" in conditions and "/" in label:
                first, second = [
                    part.strip()
                    for part in re.sub(r"\((?:crossed out|handwritten)\)", "", label).split(" / ")
                ]
                draw.rectangle((60, 90, 900, 520), fill=paper)
                draw_label(draw, (60, 90, 900, 300), [first], ink, False, True)
                draw_label(draw, (60, 310, 900, 520), [second], "#1a237e", True, False)
                steps.append("first model struck through, second handwritten")
            elif "carton" in conditions or "pallet" in conditions:
                draw.rectangle((40, 60, 920, 580), fill="#c8a165", outline="#6b4a1f", width=6)
                draw.rectangle((80, 120, 880, 520), fill="#ffffff")
                draw_label(draw, (80, 120, 880, 520), lines, ink, False, False)
                steps.append("carton/pallet label on cardboard")
            else:
                draw.rectangle((70, 100, 890, 540), fill=paper)
                draw_label(draw, (70, 100, 890, 540), lines, ink, handwriting, False)
                steps.append(
                    "specification plate"
                    if plate
                    else ("handwritten label" if handwriting else "printed label")
                )
            if "?" in label:
                steps.append("sticker over one character")
    if "glare" in conditions:
        glare = Image.new("L", (width, height), 0)
        ImageDraw.Draw(glare).ellipse((120, 40, 520, 330), fill=235)
        glare = glare.filter(ImageFilter.GaussianBlur(60))
        image = Image.composite(Image.new("RGB", (width, height), "white"), image, glare)
        steps.append("specular glare")
    if "faded" in conditions:
        image = Image.blend(image, Image.new("RGB", (width, height), "#e6e6e6"), 0.6)
        steps.append("faded printing")
    if "unclear" in conditions or "partly covered" in conditions:
        image = image.filter(ImageFilter.GaussianBlur(1.4))
        steps.append("slight defocus")
    angle = rng.uniform(-4, 4)
    image = image.rotate(angle, resample=Image.BICUBIC, fillcolor=background)
    grain = Image.effect_noise((width, height), 14).convert("RGB")
    image = Image.blend(image, grain, 0.06)
    steps.append(f"rotation {angle:.1f} degrees and sensor grain")
    name = f"{stem}.png"
    MEDIA.mkdir(parents=True, exist_ok=True)
    image.save(MEDIA / name, format="PNG")
    manifest[name] = {"kind": "image", "size": [width, height], "degradations": steps}


def main() -> int:
    """Generate all declared media, link it from the scenarios and write the hash manifest."""
    scenarios, _ = dataset.load()
    voice, photo, manifest = [], [], {}
    for item in scenarios:
        for index, turn in enumerate(item["turns"]):
            stem = f"{item['id']}-t{index}"
            if turn["kind"] == "audio":
                voice.append((stem, turn))
            elif turn["kind"] == "image":
                photo.append((stem, turn))
    make_voice(voice, manifest)
    for stem, turn in photo:
        make_photo(stem, turn, manifest)
    for item in scenarios:
        for index, turn in enumerate(item["turns"]):
            if turn["kind"] != "text":
                extension = "wav" if turn["kind"] == "audio" else "png"
                turn["spec"]["asset"] = f"media/{item['id']}-t{index}.{extension}"
    for name, entry in manifest.items():
        entry["sha256"] = hashlib.sha256((MEDIA / name).read_bytes()).hexdigest()
    (MEDIA / "MANIFEST.json").write_text(
        json.dumps(dict(sorted(manifest.items())), indent=2) + "\n", encoding="utf-8"
    )
    dataset.SCENARIO_FILE.write_text(
        json.dumps({"version": 1, "scenarios": scenarios}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"voice={len(voice)} photo={len(photo)} written to {MEDIA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
