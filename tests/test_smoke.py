"""Smoke tests for the first runnable skeleton.

Covers importability, database creation, and one sample row flowing through the
full pipeline against a temporary database (the real data/processed/seco.db is
never touched).
"""

from __future__ import annotations

import importlib

import pytest

from src.ai.risk_extract import MISSING_INFO_PHRASES, extract_brief
from src.app.streamlit_app import category_for_term
from src.collect.sample_loader import load_sample
from src.db import database
from src.pipeline import PUBLIC_SAMPLE_PATH, run_pipeline

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


def test_public_pmp_sample_loads(tmp_path):
    """The curated Luxembourg PMP sample loads with correct provenance metadata.

    The notice text is French; the English keyword extractor will not fire on most
    terms, which is expected and documented. Assertions cover provenance fields and
    the structural validity of the returned InspectionBrief only.
    """
    doc = load_sample(PUBLIC_SAMPLE_PATH)

    assert doc.source != "synthetic_sample"
    assert doc.source_url is not None
    assert doc.source_url.startswith("http")
    assert doc.title  # non-empty, parsed from TITLE: line
    assert doc.raw_text  # non-empty body text
    assert doc.clean_text  # cleaned version present

    brief = extract_brief(doc)
    assert brief.confidence == "low"
    assert brief.human_review_required is True
    assert brief.summary  # summary is always populated

    # Pipeline round-trip: document and brief are stored and retrievable.
    db_path = tmp_path / "test_public.db"
    document_id, brief_id = run_pipeline(PUBLIC_SAMPLE_PATH, db_path)
    assert document_id >= 1
    assert brief_id >= 1
    stored_brief = database.get_brief_for_document(document_id, db_path)
    assert stored_brief is not None
    assert stored_brief.human_review_required is True

    docs = database.get_documents(db_path)
    assert len(docs) == 1
    assert docs[0]["source_url"] is not None
    assert docs[0]["source_url"].startswith("http")


def test_category_for_term():
    # A known risk keyword maps to its domain (case-insensitive).
    assert category_for_term("asbestos") == "Asbestos / hazardous materials"
    assert category_for_term("  HVAC ") == "HVAC"
    # A missing-information phrase maps to the missing-information category.
    assert category_for_term("not attached") == "Missing information"
    # An unknown term falls back to "Other".
    assert category_for_term("unrelated") == "Other"
