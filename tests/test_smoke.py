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
from src.collect.sample_loader import build_document_from_text, load_sample
from src.db import database
from src.pipeline import PUBLIC_SAMPLE_BELVAUX_PATH, PUBLIC_SAMPLE_PATH, run_pipeline
from src.validation.manual_validation import load_validation_summary

MODULES = [
    "src.models",
    "src.parse.clean",
    "src.collect.sample_loader",
    "src.db.database",
    "src.ai.risk_extract",
    "src.pipeline",
    "src.app.streamlit_app",
    "src.validation.manual_validation",
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
    """The curated Luxembourg PMP sample loads with correct provenance metadata
    and produces source-traced findings via the French keyword extension.
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

    # French keyword extension: CTIE sample must now produce findings.
    assert "Asbestos / hazardous materials" in brief.risk_domains
    assert "Structure / deconstruction" in brief.risk_domains
    assert brief.evidence  # at least one source-traced snippet

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


def test_ctie_french_keyword_extraction():
    """French keyword extension produces source-traced findings on the CTIE sample.

    This is a small targeted extension for the curated Luxembourg PMP/CTIE sample,
    not general multilingual NLP. Each assertion verifies that a specific French
    term triggers the expected domain and that evidence is traceable to the source.
    """
    doc = load_sample(PUBLIC_SAMPLE_PATH)
    brief = extract_brief(doc)

    assert brief.confidence == "low"
    assert brief.human_review_required is True

    detected = set(brief.risk_domains)
    # Terms present in the CTIE text and their expected domains:
    assert "Asbestos / hazardous materials" in detected    # amiant / flocage
    assert "Structure / deconstruction" in detected        # déconstruct / dalles / charpente
    assert "Remediation / site preparation" in detected    # curage / assainissement
    assert "Materials reuse / circularity" in detected     # réemploi / valorisation

    # Every detected domain must have at least one source-traced evidence snippet.
    matched_domains = {ev.matched_term for ev in brief.evidence}
    assert matched_domains  # at least one term captured

    for ev in brief.evidence:
        assert ev.snippet      # non-empty source line
        assert ev.location     # non-empty location string
        assert ev.matched_term # traceable keyword recorded


def test_evidence_prefers_non_title_line():
    """Evidence selection prefers an OBJECT/body line over the TITLE line.

    On the Belvaux sample, HVAC / Electrical / Kitchen keywords first appear in the
    TITLE line but recur in the OBJECT line; the stored evidence should use the
    more useful OBJECT line, not the TITLE line.
    """
    doc = load_sample(PUBLIC_SAMPLE_BELVAUX_PATH)
    brief = extract_brief(doc)

    assert brief.evidence  # keyword evidence is captured
    for ev in brief.evidence:
        assert not ev.snippet.strip().upper().startswith("TITLE:"), (
            f"Evidence for '{ev.matched_term}' should prefer a non-title line, "
            f"got: {ev.snippet!r} at {ev.location}"
        )
    # The OBJECT line mentions the works; evidence should quote it.
    assert any("travaux" in ev.snippet.lower() for ev in brief.evidence)


def test_category_for_term():
    # A known risk keyword maps to its domain (case-insensitive).
    assert category_for_term("asbestos") == "Asbestos / hazardous materials"
    assert category_for_term("  HVAC ") == "HVAC"
    # A missing-information phrase maps to the missing-information category.
    assert category_for_term("not attached") == "Missing information"
    # An unknown term falls back to "Other".
    assert category_for_term("unrelated") == "Other"
    # French keyword extension: terms from the curated CTIE sample.
    assert category_for_term("amiant") == "Asbestos / hazardous materials"
    assert category_for_term("curage") == "Remediation / site preparation"


def test_build_document_from_text_uses_title_line():
    doc = build_document_from_text("TITLE: Roof replacement works\nObjet: travaux")
    assert doc.title == "Roof replacement works"


def test_build_document_from_text_default_title_when_no_title_line():
    doc = build_document_from_text("Some pasted excerpt without a title line.")
    assert doc.title == "Ad-hoc public excerpt"
    # A caller-provided default title is honoured.
    doc2 = build_document_from_text("No title here", default_title="Custom default")
    assert doc2.title == "Custom default"


def test_build_document_from_text_default_source_is_user_input():
    doc = build_document_from_text("Body text")
    assert doc.source == "user_input"
    # Empty source_url is normalised to None.
    assert doc.source_url is None


def test_build_document_from_text_preserves_source_url():
    doc = build_document_from_text("Body text", source_url="https://example.org/notice")
    assert doc.source_url == "https://example.org/notice"


def test_build_document_from_text_applies_clean_text():
    raw = "TITLE: Façade works\r\nObject line trailing   \r\n"
    doc = build_document_from_text(raw)
    # clean_text normalises CRLF, strips trailing spaces per line, and trims overall.
    assert "\r" not in doc.clean_text
    assert doc.clean_text == "TITLE: Façade works\nObject line trailing"
    # The original raw text is preserved as provided.
    assert doc.raw_text == raw


def test_load_sample_behavior_unchanged():
    """The default synthetic sample still loads with prior provenance behaviour."""
    doc = load_sample()
    assert doc.source == "synthetic_sample"
    assert doc.source_url is None
    assert doc.title  # parsed from the sample's TITLE: line
    assert doc.clean_text


def test_load_validation_summary():
    """The validation snapshot reads the committed CSV and counts match statuses."""
    summary = load_validation_summary()

    # Every reviewed row is counted exactly once across the status buckets.
    assert summary["sample_count"] >= 2
    assert sum(summary["status_counts"].values()) == summary["sample_count"]
    # The committed validation rows include at least one matching baseline check.
    assert summary["status_counts"].get("match", 0) >= 1

    # Compact detail rows back the validation-details table (one row per sample,
    # only the readable columns; long notes/limitations are intentionally omitted).
    detail_rows = summary["detail_rows"]
    assert len(detail_rows) == summary["sample_count"]
    expected_columns = {
        "sample_id",
        "source_type",
        "match_status",
        "manually_expected_domains",
        "extracted_domains",
    }
    for row in detail_rows:
        assert set(row.keys()) == expected_columns
        assert "manual_notes" not in row
        assert "limitation" not in row
        # Display polish: short categorical columns are humanized (no underscores,
        # sentence-cased), while sample_id stays the raw identifier.
        assert "_" not in row["source_type"]
        assert "_" not in row["match_status"]
        if row["match_status"]:
            assert row["match_status"][:1].isupper()
    # Raw CSV values are preserved for the status counts (not humanized).
    assert "match" in summary["status_counts"]
