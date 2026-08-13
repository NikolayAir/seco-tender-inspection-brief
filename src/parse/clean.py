"""Text normalisation for tender documents.

Normalises Unicode and line endings, trims trailing whitespace from each line,
and removes leading and trailing whitespace from the complete text. It does not
parse PDF, HTML, or layout structure.
"""

from __future__ import annotations

import unicodedata


def clean_text(raw_text: str) -> str:
    """Normalise Unicode and line endings; trim trailing and outer whitespace."""
    text = unicodedata.normalize("NFC", raw_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip()
    return cleaned
