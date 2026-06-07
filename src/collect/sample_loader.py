"""Offline data collection for the skeleton.

Loads a bundled sample tender from ``data/samples/`` into a ``TenderDocument``.
This is the no-network stand-in for a real collection step (public procurement
API / scraping), which is out of scope for the skeleton.

Two kinds of bundled sample are supported, both read fully offline:

* the synthetic sample (no provenance header), and
* manually curated public samples that carry provenance in ``#`` comment-header
  lines (``SOURCE``, ``SOURCE_URL``). Other header keys such as ``TED_NOTICE`` or
  ``REFERENCE`` stay on disk as provenance and are not part of the DB schema.
"""

from __future__ import annotations

from pathlib import Path

from src.models import TenderDocument
from src.parse.clean import clean_text

DEFAULT_SAMPLE_PATH = Path("data") / "samples" / "synthetic_sample_tender_001.txt"

DEFAULT_SOURCE = "synthetic_sample"


def _extract_title(text: str, fallback: str = "Untitled synthetic tender sample") -> str:
    """Use the 'TITLE:' line if present, else fall back to ``fallback``.

    The default fallback preserves the original bundled-sample behaviour; callers
    that load ad-hoc text can pass their own fallback title.
    """
    for line in text.split("\n"):
        if line.strip().upper().startswith("TITLE:"):
            return line.split(":", 1)[1].strip()
    return fallback


def _parse_header_metadata(full_text: str) -> dict[str, str]:
    """Read ``# KEY: value`` provenance lines from the file's comment header.

    Only ``#``-prefixed lines are considered, so document body text is never
    mistaken for metadata. Keys are upper-cased for stable lookup.
    """
    metadata: dict[str, str] = {}
    for line in full_text.split("\n"):
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        content = stripped[1:].strip()
        if ":" not in content:
            continue
        key, value = content.split(":", 1)
        metadata[key.strip().upper()] = value.strip()
    return metadata


def load_sample(sample_path: Path | str = DEFAULT_SAMPLE_PATH) -> TenderDocument:
    """Load a bundled sample file into a TenderDocument.

    Comment lines (starting with '#') are kept out of the document text. If the
    header declares ``SOURCE`` / ``SOURCE_URL`` (curated public samples), those
    are used for provenance; otherwise the file is treated as the synthetic
    sample (``source='synthetic_sample'``, no URL), preserving prior behaviour.
    """
    path = Path(sample_path)
    full_text = path.read_text(encoding="utf-8")

    metadata = _parse_header_metadata(full_text)

    body_lines = [ln for ln in full_text.split("\n") if not ln.lstrip().startswith("#")]
    raw_text = "\n".join(body_lines).strip()

    return TenderDocument(
        source=metadata.get("SOURCE", DEFAULT_SOURCE),
        source_url=metadata.get("SOURCE_URL") or None,
        title=_extract_title(raw_text),
        raw_text=raw_text,
        clean_text=clean_text(raw_text),
    )


def build_document_from_text(
    raw_text: str,
    *,
    source: str = "user_input",
    source_url: str = "",
    default_title: str = "Ad-hoc public excerpt",
) -> TenderDocument:
    """Build a ``TenderDocument`` from ad-hoc pasted text, in memory only.

    Reuses ``clean_text`` and the ``TITLE:`` extraction logic. Nothing is read
    from or written to disk or SQLite, and ``extract_brief`` is not called here;
    this only constructs the document so a caller can analyse pasted text without
    persisting it. ``load_sample`` behaviour is unchanged.

    An empty ``source_url`` is normalised to ``None`` to match the model's
    convention for documents without a public URL.
    """
    return TenderDocument(
        source=source,
        source_url=source_url or None,
        title=_extract_title(raw_text, fallback=default_title),
        raw_text=raw_text,
        clean_text=clean_text(raw_text),
    )
