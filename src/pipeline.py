"""Single CLI entry point for the skeleton vertical slice.

Wires the layers together:
    load synthetic sample -> clean -> store document -> extract brief -> store brief.

Run from the repository root:
    python -m src.pipeline
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.ai.risk_extract import extract_brief
from src.collect.sample_loader import DEFAULT_SAMPLE_PATH, load_sample
from src.db import database


def run_pipeline(
    sample_path: Path | str = DEFAULT_SAMPLE_PATH,
    db_path: Path | str = database.DEFAULT_DB_PATH,
) -> tuple[int, int]:
    """Run the full skeleton flow and return (document_id, brief_id)."""
    database.init_db(db_path)

    document = load_sample(sample_path)
    document_id = database.insert_document(document, db_path)

    brief = extract_brief(document)
    brief_id = database.insert_brief(document_id, brief, db_path)

    return document_id, brief_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Tender-to-Inspection Brief skeleton pipeline.")
    parser.add_argument(
        "--sample", default=str(DEFAULT_SAMPLE_PATH), help="Path to a sample tender text file."
    )
    parser.add_argument(
        "--db", default=str(database.DEFAULT_DB_PATH), help="Path to the SQLite database file."
    )
    args = parser.parse_args()

    document_id, brief_id = run_pipeline(args.sample, args.db)
    print(
        f"Pipeline complete (synthetic sample). "
        f"document_id={document_id}, brief_id={brief_id}, db={args.db}"
    )
    print("Reminder: keyword placeholder output for human review only; not real AI.")


if __name__ == "__main__":
    main()
