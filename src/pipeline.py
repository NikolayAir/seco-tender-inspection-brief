"""Single CLI entry point for the vertical slice.

Wires the layers together:
    load sample -> clean -> store document -> extract brief -> store brief.

Run from the repository root:
    python -m src.pipeline                  # ingests all bundled samples
    python -m src.pipeline --sample <path>  # ingests one specific sample file
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.ai.risk_extract import extract_brief
from src.collect.sample_loader import DEFAULT_SAMPLE_PATH, load_sample
from src.db import database
from src.provenance import build_processing_run

PUBLIC_SAMPLE_PATH = Path("data") / "samples" / "public_lu_pmp_ctie_001.txt"
PUBLIC_SAMPLE_BELVAUX_PATH = Path("data") / "samples" / "public_lu_pmp_snhbm_belvaux_001.txt"

# Samples ingested by the CLI by default: the synthetic sample (offline tests)
# plus the manually curated public samples. Each is stored as its own document;
# idempotency is handled per (source, title) in run_pipeline.
BUNDLED_SAMPLES: list[Path] = [
    DEFAULT_SAMPLE_PATH,
    PUBLIC_SAMPLE_PATH,
    PUBLIC_SAMPLE_BELVAUX_PATH,
]


def run_pipeline(
    sample_path: Path | str = DEFAULT_SAMPLE_PATH,
    db_path: Path | str = database.DEFAULT_DB_PATH,
) -> tuple[int, int]:
    """Run the full pipeline flow and return (document_id, brief_id).

    Safe to run repeatedly: the pipeline reuses an existing document found by
    (source, title), so ordinary re-runs update that logical document instead of
    inserting duplicates. Each
    execution appends a traceable processing run and preserves its linked brief.
    """
    database.init_db(db_path)

    document = load_sample(sample_path)
    existing_id = database.find_document_id(document.source, document.title, db_path)
    if existing_id is None:
        document_id = database.insert_document(document, db_path)
    else:
        document_id = existing_id
        database.update_document(document_id, document, db_path)

    brief = extract_brief(document)
    processing_run = build_processing_run(document_id, document)
    _, brief_id = database.insert_processing_result(
        processing_run,
        brief,
        db_path,
    )

    return document_id, brief_id


def ingest_bundled_samples(
    db_path: Path | str = database.DEFAULT_DB_PATH,
) -> list[tuple[int, int]]:
    """Run the pipeline over every bundled sample once.

    Returns a list of (document_id, brief_id) per sample. Reused by the Streamlit
    app to initialise the demo database when it is missing or empty. Fully offline;
    only the committed bundled sample files are ingested.
    """
    return [run_pipeline(sample_path, db_path) for sample_path in BUNDLED_SAMPLES]


def main() -> None:
    parser = argparse.ArgumentParser(description="Tender-to-Inspection Brief pipeline.")
    parser.add_argument(
        "--sample",
        default=None,
        help=(
            "Path to a single sample tender text file. "
            "Omit to ingest all bundled samples (synthetic + public curated)."
        ),
    )
    parser.add_argument(
        "--db", default=str(database.DEFAULT_DB_PATH), help="Path to the SQLite database file."
    )
    args = parser.parse_args()

    samples = [Path(args.sample)] if args.sample else BUNDLED_SAMPLES
    for sample_path in samples:
        document_id, brief_id = run_pipeline(sample_path, args.db)
        print(f"  {sample_path.name}: document_id={document_id}, brief_id={brief_id}")

    print(f"Pipeline complete. {len(samples)} sample(s) ingested.")
    print(f"Briefs saved to SQLite: {args.db}")
    print("Next step: streamlit run src/app/streamlit_app.py")
    print(
        "Note: output is a transparent rule-based domain-classification baseline "
        "for reviewer assistance only. It does not make legal, regulatory, "
        "compliance, safety, or engineering decisions."
    )


if __name__ == "__main__":
    main()
