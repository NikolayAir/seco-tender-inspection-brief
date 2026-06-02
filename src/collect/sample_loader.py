"""Offline data collection for the skeleton.

Loads the bundled synthetic sample tender from ``data/samples/`` into a
``TenderDocument``. This is the no-network stand-in for a real collection step
(public procurement API / scraping), which is out of scope for the skeleton.
"""

from __future__ import annotations

from pathlib import Path

from src.models import TenderDocument
from src.parse.clean import clean_text

DEFAULT_SAMPLE_PATH = Path("data") / "samples" / "synthetic_sample_tender_001.txt"


def _extract_title(text: str) -> str:
    """Use the 'TITLE:' line if present, else fall back to a generic title."""
    for line in text.split("\n"):
        if line.strip().upper().startswith("TITLE:"):
            return line.split(":", 1)[1].strip()
    return "Untitled synthetic tender sample"


def load_sample(sample_path: Path | str = DEFAULT_SAMPLE_PATH) -> TenderDocument:
    """Load the synthetic sample file into a TenderDocument.

    Comment lines (starting with '#') are kept out of the document text but the
    file remains clearly labelled as synthetic on disk.
    """
    path = Path(sample_path)
    full_text = path.read_text(encoding="utf-8")

    body_lines = [ln for ln in full_text.split("\n") if not ln.lstrip().startswith("#")]
    raw_text = "\n".join(body_lines).strip()

    return TenderDocument(
        source="synthetic_sample",
        source_url=None,
        title=_extract_title(raw_text),
        raw_text=raw_text,
        clean_text=clean_text(raw_text),
    )
