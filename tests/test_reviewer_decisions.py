"""Focused tests for persisted reviewer-decision events."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.db import database
from src.models import (
    EvidenceSnippet,
    InspectionBrief,
    ProcessingRun,
    ReviewerDecision,
    TenderDocument,
)


def _persist_test_brief(tmp_path):
    db_path = tmp_path / "reviewer_decisions.db"
    database.init_db(db_path)

    document = TenderDocument(
        source="test_source",
        source_url="https://example.org/tender",
        title="Reviewer decision test tender",
        raw_text="Fire-safety and facade works. Drawings are not attached.",
        clean_text="Fire-safety and facade works. Drawings are not attached.",
    )
    document_id = database.insert_document(document, db_path)

    processing_run = ProcessingRun(
        document_id=document_id,
        processed_at=datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc),
        extractor_name="deterministic_keyword_baseline",
        extractor_version="1.0.0",
        brief_schema_version="1.0.0",
        source_content_fingerprint="a" * 64,
    )
    _, brief_id = database.insert_processing_result(
        processing_run,
        InspectionBrief(
            summary="A persisted brief for reviewer-decision testing.",
            risk_domains=["Fire safety", "Building envelope"],
            missing_info=["Drawings are not attached."],
            evidence=[
                EvidenceSnippet(
                    snippet="Fire-safety and facade works.",
                    matched_term="fire",
                    location="line 1",
                )
            ],
        ),
        db_path,
    )

    return db_path, document_id, brief_id


def test_schema_creation_is_additive_and_idempotent(tmp_path) -> None:
    db_path, document_id, brief_id = _persist_test_brief(tmp_path)

    with database.connect(db_path) as conn:
        conn.execute("DROP TABLE reviewer_decisions")

    database.init_db(db_path)
    database.init_db(db_path)

    with database.connect(db_path) as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        stored_brief_count = conn.execute(
            "SELECT COUNT(*) AS count FROM briefs WHERE id = ?",
            (brief_id,),
        ).fetchone()["count"]
        stored_document_count = conn.execute(
            "SELECT COUNT(*) AS count FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()["count"]

    assert "reviewer_decisions" in tables
    assert stored_brief_count == 1
    assert stored_document_count == 1


def test_reviewer_decision_persists_and_reloads_in_utc(tmp_path) -> None:
    db_path, _, brief_id = _persist_test_brief(tmp_path)

    decision_id = database.insert_reviewer_decision(
        ReviewerDecision(
            brief_id=brief_id,
            target_type="risk_domain",
            target_index=0,
            state="needs_follow_up",
            note="  Confirm the referenced drawings.  ",
            decided_at=datetime(
                2026,
                8,
                5,
                10,
                30,
                tzinfo=timezone(timedelta(hours=2)),
            ),
        ),
        db_path,
    )

    history = database.get_reviewer_decision_history(brief_id, db_path)

    assert len(history) == 1
    assert history[0].id == decision_id
    assert history[0].brief_id == brief_id
    assert history[0].target_type == "risk_domain"
    assert history[0].target_index == 0
    assert history[0].state == "needs_follow_up"
    assert history[0].note == "Confirm the referenced drawings."
    assert history[0].decided_at == datetime(
        2026,
        8,
        5,
        8,
        30,
        tzinfo=timezone.utc,
    )


def test_state_changes_append_history_and_select_latest_event(tmp_path) -> None:
    db_path, _, brief_id = _persist_test_brief(tmp_path)

    first_id = database.insert_reviewer_decision(
        ReviewerDecision(
            brief_id=brief_id,
            target_type="risk_domain",
            target_index=0,
            state="needs_follow_up",
            note="Check the drawings.",
            decided_at=datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc),
        ),
        db_path,
    )
    second_id = database.insert_reviewer_decision(
        ReviewerDecision(
            brief_id=brief_id,
            target_type="risk_domain",
            target_index=0,
            state="accepted",
            note="Drawings confirmed.",
            decided_at=datetime(2026, 8, 5, 9, 0, tzinfo=timezone.utc),
        ),
        db_path,
    )
    missing_info_id = database.insert_reviewer_decision(
        ReviewerDecision(
            brief_id=brief_id,
            target_type="missing_info",
            target_index=0,
            state="rejected",
            note=None,
            decided_at=datetime(2026, 8, 5, 9, 30, tzinfo=timezone.utc),
        ),
        db_path,
    )

    history = database.get_reviewer_decision_history(brief_id, db_path)
    latest = database.get_latest_reviewer_decisions(brief_id, db_path)

    assert [event.id for event in history] == [
        first_id,
        second_id,
        missing_info_id,
    ]
    assert [event.state for event in history[:2]] == [
        "needs_follow_up",
        "accepted",
    ]
    assert latest[("risk_domain", 0)].id == second_id
    assert latest[("risk_domain", 0)].state == "accepted"
    assert latest[("missing_info", 0)].id == missing_info_id
    assert latest[("missing_info", 0)].state == "rejected"


@pytest.mark.parametrize(
    ("target_type", "target_index"),
    [
        ("risk_domain", 2),
        ("missing_info", 1),
    ],
)
def test_insert_rejects_target_index_outside_linked_brief(
    tmp_path,
    target_type,
    target_index,
) -> None:
    db_path, _, brief_id = _persist_test_brief(tmp_path)

    decision = ReviewerDecision(
        brief_id=brief_id,
        target_type=target_type,
        target_index=target_index,
        state="accepted",
        decided_at=datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError, match="target_index"):
        database.insert_reviewer_decision(decision, db_path)


def test_insert_rejects_unknown_brief(tmp_path) -> None:
    db_path = tmp_path / "unknown_brief.db"
    database.init_db(db_path)

    decision = ReviewerDecision(
        brief_id=999,
        target_type="risk_domain",
        target_index=0,
        state="accepted",
        decided_at=datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError, match="does not reference a persisted brief"):
        database.insert_reviewer_decision(decision, db_path)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("target_type", "review_question"),
        ("state", "unreviewed"),
    ],
)
def test_model_rejects_unsupported_target_types_and_states(
    field_name,
    invalid_value,
) -> None:
    payload = {
        "brief_id": 1,
        "target_type": "risk_domain",
        "target_index": 0,
        "state": "accepted",
        "decided_at": datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc),
    }
    payload[field_name] = invalid_value

    with pytest.raises(ValidationError):
        ReviewerDecision(**payload)


def test_model_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        ReviewerDecision(
            brief_id=1,
            target_type="risk_domain",
            target_index=0,
            state="accepted",
            decided_at=datetime(2026, 8, 5, 8, 0),
        )


def test_note_normalization_and_length_validation() -> None:
    blank_note = ReviewerDecision(
        brief_id=1,
        target_type="risk_domain",
        target_index=0,
        state="accepted",
        note="   ",
        decided_at=datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc),
    )

    assert blank_note.note is None

    with pytest.raises(ValidationError):
        ReviewerDecision(
            brief_id=1,
            target_type="risk_domain",
            target_index=0,
            state="accepted",
            note="x" * 2001,
            decided_at=datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc),
        )


def test_recording_decision_does_not_mutate_generated_brief(tmp_path) -> None:
    db_path, document_id, brief_id = _persist_test_brief(tmp_path)

    before = database.get_brief_for_document(document_id, db_path)
    assert before is not None

    database.insert_reviewer_decision(
        ReviewerDecision(
            brief_id=brief_id,
            target_type="risk_domain",
            target_index=0,
            state="accepted",
            note="Human-authored review state.",
            decided_at=datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc),
        ),
        db_path,
    )

    after = database.get_brief_for_document(document_id, db_path)

    assert after is not None
    assert after.model_dump() == before.model_dump()
    assert after.evidence == before.evidence
