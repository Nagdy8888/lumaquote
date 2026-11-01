"""Voice-specific entry point over the shared fenced media lifecycle."""

from .media import process_media


def process_audio(job):
    """Process only audio jobs through offline normalization and one budget-reserved transcription attempt."""
    return process_media(job, "audio")
