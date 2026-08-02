"""Focused tests for the versioned inspection-brief JSON export contract."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.exports import (
    BRIEF_EXPORT_SCHEMA_VERSION,
    ExportDocument,
    ExportProcessingRun,
    VersionedBriefExport,
    serialize_brief_export,
)
from src.models import EvidenceSnippet, InspectionBrief


def _export_payload() -> VersionedBriefExport:
    return VersionedBriefExport(
        document=ExportDocument(
            id=7,
            source="public_sample",
            source_url="https://example.org/tender",
            title="Building renovation works",
        ),
        processing_run=ExportProcessingRun(
            id=11,
            processed_at=datetime(
                2026,
                8,
                1,
                20,
                30,
                tzinfo=timezone(timedelta(hours=2)),
            ),
            extractor_name="deterministic_keyword_baseline",
            extractor_version="1.0.0",
            brief_schema_version="1.0.0",
            source_content_fingerprint="a" * 64,
        ),
        brief_id=13,
        brief=InspectionBrief(
            summary="Renovation works requiring structured technical review.",
            technical_scopes=["Facade"],
            risk_domains=["Fire safety"],
            missing_info=["Drawings not attached."],
            review_questions=["Are fire-safety drawings available?"],
            evidence=[
                EvidenceSnippet(
                    snippet="Fire-safety works are included.",
                    matched_term="fire",
                    location="line 4",
                )
            ],
        ),
    )


def test_versioned_export_has_stable_structure_and_metadata() -> None:
    payload = _export_payload()
    exported = json.loads(serialize_brief_export(payload))

    assert exported["export_schema_version"] == BRIEF_EXPORT_SCHEMA_VERSION
    assert exported["document"] == {
        "id": 7,
        "source": "public_sample",
        "source_url": "https://example.org/tender",
        "title": "Building renovation works",
    }
    assert exported["processing_run"]["id"] == 11
    assert exported["processing_run"]["processed_at"] == "2026-08-01T18:30:00Z"
    assert exported["processing_run"]["source_content_fingerprint"] == "a" * 64
    assert exported["brief_id"] == 13
    assert exported["brief"]["risk_domains"] == ["Fire safety"]
    assert exported["brief"]["evidence"][0]["matched_term"] == "fire"
    assert exported["brief"]["human_review_required"] is True


def test_serialization_is_byte_stable_for_same_payload() -> None:
    payload = _export_payload()

    first = serialize_brief_export(payload)
    second = serialize_brief_export(payload)

    assert first == second
    assert first.endswith("\n")
    assert "Building renovation works" in first


def test_processing_timestamp_is_normalized_to_utc() -> None:
    payload = _export_payload()

    assert payload.processing_run.processed_at == datetime(
        2026,
        8,
        1,
        18,
        30,
        tzinfo=timezone.utc,
    )


def test_export_rejects_naive_processing_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        ExportProcessingRun(
            id=11,
            processed_at=datetime(2026, 8, 1, 18, 30),
            extractor_name="deterministic_keyword_baseline",
            extractor_version="1.0.0",
            brief_schema_version="1.0.0",
            source_content_fingerprint="a" * 64,
        )


def test_export_rejects_invalid_source_fingerprint() -> None:
    with pytest.raises(ValidationError):
        ExportProcessingRun(
            id=11,
            processed_at=datetime(2026, 8, 1, 18, 30, tzinfo=timezone.utc),
            extractor_name="deterministic_keyword_baseline",
            extractor_version="1.0.0",
            brief_schema_version="1.0.0",
            source_content_fingerprint="not-a-sha256-fingerprint",
        )
