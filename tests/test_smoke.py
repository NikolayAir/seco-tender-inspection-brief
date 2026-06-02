"""Smoke tests for the first runnable skeleton.

Covers importability, database creation, and one sample row flowing through the
full pipeline against a temporary database (the real data/processed/seco.db is
never touched).
"""

from __future__ import annotations

import importlib

import pytest

from src.ai.risk_extract import MISSING_INFO_PHRASES, extract_brief
from src.collect.sample_loader import load_sample
from src.db import database
from src.pipeline import run_pipeline

MODULES = [
    "src.models",
    "src.parse.clean",
    "src.collect.sample_loader",
    "src.db.database",
    "src.ai.risk_extract",
    "src.pipeline",
    "src.app.streamlit_app",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_imports(module_name):
    importlib.import_module(module_name)


def test_init_db_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    database.init_db(db_path)
    with database.connect(db_path) as conn:
        names = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert {"documents", "briefs"}.issubset(names)


def test_sample_flow(tmp_path):
    db_path = tmp_path / "test.db"
    document_id, brief_id = run_pipeline(db_path=db_path)

    assert document_id == 1
    assert brief_id == 1

    documents = database.get_documents(db_path)
    assert len(documents) == 1

    brief = database.get_brief_for_document(document_id, db_path)
    assert brief is not None
    assert brief.summary
    assert brief.confidence == "low"
    assert brief.human_review_required is True
    assert brief.evidence  # at least one source-traced snippet
    assert brief.missing_info  # missing-information signals are captured and stored

    # The synthetic sample seeds these domains; the keyword rules must find them.
    assert "Fire safety" in brief.risk_domains
    assert "Asbestos / hazardous materials" in brief.risk_domains


def test_pipeline_idempotent(tmp_path):
    db_path = tmp_path / "test.db"

    # Run the pipeline twice against the same database.
    run_pipeline(db_path=db_path)
    document_id, brief_id = run_pipeline(db_path=db_path)

    # Exactly one document and one brief, regardless of run count.
    documents = database.get_documents(db_path)
    assert len(documents) == 1

    with database.connect(db_path) as conn:
        brief_count = conn.execute("SELECT COUNT(*) AS c FROM briefs").fetchone()["c"]
    assert brief_count == 1

    # The single brief is correctly linked to the single document.
    assert documents[0]["id"] == document_id
    with database.connect(db_path) as conn:
        linked_doc_id = conn.execute(
            "SELECT document_id FROM briefs WHERE id = ?", (brief_id,)
        ).fetchone()["document_id"]
    assert linked_doc_id == document_id


def test_missing_info_detected():
    brief = extract_brief(load_sample())

    # The synthetic sample explicitly states documents are missing.
    assert len(brief.missing_info) >= 2
    joined = " ".join(brief.missing_info).lower()
    assert "not attached" in joined
    assert "requested separately" in joined

    # Missing-info findings are source-traced via evidence snippets.
    matched_terms = {ev.matched_term for ev in brief.evidence}
    assert matched_terms & set(MISSING_INFO_PHRASES)
