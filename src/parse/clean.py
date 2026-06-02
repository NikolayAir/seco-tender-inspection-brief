"""Minimal text cleaning for the skeleton.

Only whitespace/encoding normalization for now. Real parsing (PDF, HTML, layout)
is intentionally out of scope for the first skeleton.
"""

from __future__ import annotations

import unicodedata


def clean_text(raw_text: str) -> str:
    """Normalize unicode and collapse excess blank lines / trailing spaces."""
    text = unicodedata.normalize("NFC", raw_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip()
    return cleaned
