"""Smoke tests for the first runnable skeleton.

Covers importability, database creation, and one sample row flowing through the
full pipeline against a temporary database (the real data/processed/seco.db is
never touched).
"""

from __future__ import annotations

import importlib

import pytest

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

    # The synthetic sample seeds these domains; the keyword rules must find them.
    assert "Fire safety" in brief.risk_domains
    assert "Asbestos / hazardous materials" in brief.risk_domains
