"""Shared Pydantic models for the Tender-to-Inspection Brief MVP.

These models are intentionally simple and shared across the storage, extraction,
and UI layers so the structured source document and the inspection-preparation
brief have one schema.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TenderDocument(BaseModel):
    """A single tender/public-notice document used by the MVP pipeline."""

    source: str = Field(description="Where the document came from, e.g. 'synthetic_sample'.")
    source_url: str | None = Field(
        default=None, description="Public URL if available; None for offline samples."
    )
    title: str = Field(description="Short human-readable project/document title.")
    raw_text: str = Field(description="Original text as loaded.")
    clean_text: str = Field(description="Whitespace/encoding-normalized text.")


class EvidenceSnippet(BaseModel):
    """A short piece of source text supporting a detected review domain.

    Evidence is what ties a finding back to the source document, which is the
    core value of the product. In this MVP baseline, evidence comes from the
    rule-based keyword-to-domain extraction step.
    """

    snippet: str = Field(description="Short quoted text from the source.")
    matched_term: str = Field(description="Keyword or phrase that triggered the match.")
    location: str = Field(description="Approximate location, e.g. 'line 12'.")


class InspectionBrief(BaseModel):
    """The evidence-based inspection-preparation brief for one document.

    This supports human technical review only. It is not a compliance, legal,
    safety, regulatory, or engineering decision.
    """

    summary: str = Field(description="Short, neutral project summary.")
    technical_scopes: list[str] = Field(
        default_factory=list, description="Detected technical scopes."
    )
    risk_domains: list[str] = Field(
        default_factory=list,
        description="Potential SECO-relevant technical review domains.",
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
        default="low",
        description="Qualitative confidence; always 'low' in this MVP baseline.",
    )
    human_review_required: bool = Field(
        default=True, description="Always True; output assists humans, it does not decide."
    )
