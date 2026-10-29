"""Real restricted-container parsing tests; no model or external-provider requests."""

import io
import wave

import pytest
from luma.core.errors import DomainError
from luma.features.media.sandbox import process_file
from PIL import Image
from reportlab.pdfgen.canvas import Canvas


def test_native_pdf_retains_original_page_text():
    """The actual offline sandbox preserves native evidence text and reports its original page grouping."""
    stream = io.BytesIO()
    canvas = Canvas(stream)
    canvas.drawString(30, 750, "Synthetic DL-002 product, 18W, 4000K. Test evidence only.")
    canvas.save()
    result, normalized = process_file("pdf", stream.getvalue())
    assert "DL-002" in result["pages"][0]
    assert normalized is None


def test_image_is_normalized_without_metadata():
    """A real supported image becomes bounded JPEG bytes rather than arbitrary caller-selected output."""
    output = io.BytesIO()
    Image.new("RGB", (160, 100), "white").save(output, format="PNG")
    metadata, data = process_file("image", output.getvalue())
    assert metadata["width"] == 160 and metadata["height"] == 100
    assert data[:2] == b"\xff\xd8"


@pytest.mark.parametrize(
    "kind,payload", [("pdf", b"not a PDF"), ("image", b"not an image"), ("audio", b"not audio")]
)
def test_corrupt_files_are_rejected(kind, payload):
    """A claimed extension or operation cannot make unrelated bytes a trusted document or media file."""
    with pytest.raises(DomainError):
        process_file(kind, payload)


def test_overlong_audio_is_rejected_before_transcription():
    """A compressed or ordinary input cannot bypass the actual decoded 120-second duration boundary."""
    data = io.BytesIO()
    with wave.open(data, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0\0" * 16000 * 121)
    with pytest.raises(DomainError):
        process_file("audio", data.getvalue())
