"""Regression test: extracted domains must match the manual validation CSV.

Loads ``data/labels/manual_validation_v1.csv`` and for each row re-runs the
keyword extractor on the corresponding sample. Asserts that the set of
extracted domains still matches the ``extracted_domains`` column recorded at
validation time.

Purpose: catch silent regressions if the keyword dictionary is ever changed.
This is NOT a precision/recall test; it does not evaluate correctness against
an independent gold standard.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.ai.risk_extract import extract_brief
from src.collect.sample_loader import load_sample
from src.pipeline import PUBLIC_SAMPLE_PATH

VALIDATION_CSV = Path("data/labels/manual_validation_v1.csv")

SAMPLE_PATHS: dict[str, Path] = {
    "synthetic_001": Path("data/samples/synthetic_sample_tender_001.txt"),
    "public_ctie_001": PUBLIC_SAMPLE_PATH,
}


def _load_validation_rows() -> list[dict[str, str]]:
    with VALIDATION_CSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _parse_domains(cell: str) -> set[str]:
    return {d.strip() for d in cell.split(";") if d.strip()}


@pytest.mark.parametrize("row", _load_validation_rows(), ids=lambda r: r["sample_id"])
def test_extracted_domains_match_validation_csv(row: dict[str, str]) -> None:
    """Extractor output must reproduce the domains recorded in the validation CSV.

    If this test fails after a keyword change, update the CSV and manual_notes
    to reflect the new extractor behaviour; do not silently patch the test.
    """
    sample_id = row["sample_id"]
    sample_path = SAMPLE_PATHS.get(sample_id)
    assert sample_path is not None, f"No sample path registered for sample_id={sample_id!r}"

    doc = load_sample(sample_path)
    brief = extract_brief(doc)

    recorded = _parse_domains(row["extracted_domains"])
    actual = set(brief.risk_domains)

    assert actual == recorded, (
        f"[{sample_id}] Extracted domains have diverged from the validation CSV.\n"
        f"  CSV recorded : {sorted(recorded)}\n"
        f"  Extractor now: {sorted(actual)}\n"
        "Update data/labels/manual_validation_v1.csv and manual_notes if the change is intentional."
    )
