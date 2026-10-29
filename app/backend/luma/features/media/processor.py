"""Fixed operations executed only inside the resource-limited, offline sandbox."""

import io
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


def inspect_pdf(path: Path) -> dict:
    """Extract bounded native PDF page text; reject scans, encryption, and oversized documents."""
    if path.stat().st_size > 20 * 1024 * 1024 or path.read_bytes()[:5] != b"%PDF-":
        raise ValueError("invalid_pdf")
    reader = PdfReader(path)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 50:
        raise ValueError("unsupported_pdf")
    pages = []
    total = 0
    for page in reader.pages:
        text = page.extract_text() or ""
        total += len(text)
        if total > 1_000_000:
            raise ValueError("pdf_text_limit")
        if len(text.strip()) < 15:
            raise ValueError("native_text_required")
        pages.append(text)
    return {"kind": "pdf", "pages": pages}


def inspect_image(path: Path) -> dict:
    """Normalize one bounded actual JPEG/PNG/WebP image and discard metadata before model input."""
    if path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("image_byte_limit")
    Image.MAX_IMAGE_PIXELS = 12_000_000
    with Image.open(path) as image:
        if image.format not in ("JPEG", "PNG", "WEBP") or image.width * image.height > 12_000_000:
            raise ValueError("unsupported_image")
        image.load()
        image = image.convert("RGB")
        image.thumbnail((1600, 1600))
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85)
        Path("/output/normalized.jpg").write_bytes(output.getvalue())
        return {"kind": "image", "width": image.width, "height": image.height, "output": "normalized.jpg"}


def inspect_audio(path: Path) -> dict:
    """Probe and decode at most 120 seconds to bounded mono WAV with no network protocols available."""
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("audio_byte_limit")
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        check=True,
        timeout=15,
    )
    info = json.loads(probe.stdout)
    streams = info.get("streams", [])
    if not streams or any(stream.get("codec_type") != "audio" for stream in streams):
        raise ValueError("audio_only_required")
    duration = float(info.get("format", {}).get("duration", 0))
    if not 0 < duration <= 120:
        raise ValueError("audio_duration_limit")
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(path),
            "-t",
            "120",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-map_metadata",
            "-1",
            "/output/normalized.wav",
        ],
        capture_output=True,
        check=True,
        timeout=25,
    )
    return {"kind": "audio", "duration": duration, "output": "normalized.wav"}


def main():
    """Dispatch one allowlisted parser operation and emit bounded machine-readable metadata without exception details."""
    operation = sys.argv[1]
    operations = {"pdf": inspect_pdf, "image": inspect_image, "audio": inspect_audio}
    if operation not in operations:
        raise ValueError("unsupported_operation")
    result = operations[operation](Path("/input/file"))
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"error": "file_processing_rejected"}))
        sys.exit(2)
