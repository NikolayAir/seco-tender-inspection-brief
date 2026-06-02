"""Shared pydantic models for the Tender-to-Inspection Brief MVP.

These models are intentionally simple and shared across the storage, extraction,
and UI layers so the structured record and the inspection brief have one schema.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TenderDocument(BaseModel):
    """A single (synthetic, in this skeleton) tender document."""

    source: str = Field(description="Where the document came from, e.g. 'synthetic_sample'.")
    source_url: str | None = Field(
        default=None, description="Public URL if available; None for offline samples."
    )
    title: str = Field(description="Short human-readable project/document title.")
    raw_text: str = Field(description="Original text as loaded.")
    clean_text: str = Field(description="Whitespace/encoding-normalized text.")


class EvidenceSnippet(BaseModel):
    """A short piece of source text supporting a detected domain.

    Evidence is what ties a finding back to the source document, which is the
    core value of the product. In this skeleton it comes from the keyword scan.
    """

    snippet: str = Field(description="Short quoted text from the source.")
    matched_term: str = Field(description="Keyword that triggered the match.")
    location: str = Field(description="Approximate location, e.g. 'line 12'.")


class InspectionBrief(BaseModel):
    """The evidence-based inspection-preparation brief for one document.

    This supports human technical review only. It is not a compliance, legal,
    safety, or engineering decision.
    """

    summary: str = Field(description="Short, neutral project summary.")
    technical_scopes: list[str] = Field(
        default_factory=list, description="Detected technical scopes."
    )
    risk_domains: list[str] = Field(
        default_factory=list, description="Potential SECO-relevant review domains."
    )
    missing_info: list[str] = Field(
        default_factory=list, description="Information gaps noticed in the source."
    )
    review_questions: list[str] = Field(
        default_factory=list, description="Suggested questions for the reviewer."
    )
    evidence: list[EvidenceSnippet] = Field(
        default_factory=list, description="Source snippets backing the findings."
    )
    confidence: str = Field(
        default="low", description="Qualitative confidence; always 'low' in this skeleton."
    )
    human_review_required: bool = Field(
        default=True, description="Always True; output assists humans, it does not decide."
    )
