"""Versioned JSON export contract for persisted inspection briefs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.models import InspectionBrief

BRIEF_EXPORT_SCHEMA_VERSION = "1.0.0"


class ExportDocument(BaseModel):
    """Stable public document metadata included in a brief export."""

    id: int = Field(gt=0, description="Stored document identifier.")
    source: str = Field(description="Source label stored with the document.")
    source_url: str | None = Field(
        default=None,
        description="Public source URL when available.",
    )
    title: str = Field(description="Human-readable document title.")


class ExportProcessingRun(BaseModel):
    """Processing metadata identifying how the exported brief was produced."""

    id: int = Field(gt=0, description="Stored processing-run identifier.")
    processed_at: datetime = Field(
        description="Timezone-aware processing timestamp normalized to UTC."
    )
    extractor_name: str = Field(description="Stable extraction-method identifier.")
    extractor_version: str = Field(description="Extraction implementation version.")
    brief_schema_version: str = Field(
        description="Structured inspection-brief schema version."
    )
    source_content_fingerprint: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 fingerprint of the normalized source text.",
    )

    @field_validator("processed_at")
    @classmethod
    def normalize_processed_at(cls, value: datetime) -> datetime:
        """Require an aware timestamp and normalize it to UTC."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("processed_at must be timezone-aware")
        return value.astimezone(timezone.utc)


class VersionedBriefExport(BaseModel):
    """Stable JSON representation of one persisted inspection brief."""

    export_schema_version: Literal["1.0.0"] = BRIEF_EXPORT_SCHEMA_VERSION
    document: ExportDocument
    processing_run: ExportProcessingRun
    brief_id: int = Field(gt=0, description="Stored inspection-brief identifier.")
    brief: InspectionBrief


def serialize_brief_export(payload: VersionedBriefExport) -> str:
    """Serialize an export deterministically as UTF-8-compatible JSON text."""
    return (
        json.dumps(
            payload.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
