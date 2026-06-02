"""Streamlit UI for the Tender-to-Inspection Brief MVP (read-only).

Run from the repository root:
    streamlit run src/app/streamlit_app.py

It reads the SQLite database produced by ``python -m src.pipeline`` and displays
stored documents and their keyword-placeholder inspection briefs. Source labeling
is conditional: synthetic documents are flagged as offline test data; curated
public documents show the verified source URL.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `streamlit run src/app/streamlit_app.py` to import the `src` package by
# ensuring the repository root is on the path.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from src.ai.risk_extract import KEYWORD_DOMAINS, MISSING_INFO_PHRASES  # noqa: E402
from src.db import database  # noqa: E402
from src.models import EvidenceSnippet  # noqa: E402


def category_for_term(term: str) -> str:
    """Map a matched term to a readable category for the evidence table.

    Display-only label lookup (not extraction logic): missing-information phrases
    become "Missing information", risk keywords map to their domain. The term is
    normalized with lower().strip() so matching is case-insensitive.
    """
    normalized = term.lower().strip()
    if normalized in {p.lower().strip() for p in MISSING_INFO_PHRASES}:
        return "Missing information"
    for domain, keywords in KEYWORD_DOMAINS.items():
        if normalized in {k.lower().strip() for k in keywords}:
            return domain
    return "Other"


def evidence_rows(evidence: list[EvidenceSnippet]) -> list[dict]:
    """Build list-of-dict rows for st.dataframe (no pandas dependency)."""
    return [
        {
            "Category": category_for_term(ev.matched_term),
            "Matched term": ev.matched_term,
            "Location": ev.location,
            "Snippet": ev.snippet,
        }
        for ev in evidence
    ]


def _bullets(items: list[str], empty_text: str) -> None:
    """Render a list of strings as markdown bullets, or an italic empty note."""
    if not items:
        st.markdown(f"*{empty_text}*")
        return
    st.markdown("\n".join(f"- {item}" for item in items))


def render() -> None:
    """Render the read-only inspection-brief dashboard."""
    st.set_page_config(page_title="Tender-to-Inspection Brief", layout="wide")

    st.title("Tender-to-Inspection Brief")
    st.caption(
        "Reviewer-assistance MVP - supports human technical review only. "
        "It does not make legal, regulatory, safety, compliance, or engineering decisions."
    )
    st.warning(
        "Prototype note: extraction uses a transparent keyword baseline (not full AI/NLP). "
        "Output supports human technical review only."
    )

    documents = database.get_documents()

    if not documents:
        st.info(
            "No documents found in the database. "
            "Run `python -m src.pipeline` from the repository root first, then refresh."
        )
        st.stop()

    labels = {f"#{d['id']} - {d['title']}": d for d in documents}
    choice = st.selectbox("Select a document", list(labels.keys()))
    document = labels[choice]

    is_synthetic = document["source"] == "synthetic_sample"
    if is_synthetic:
        st.info(
            "This document is synthetic sample data for offline skeleton testing. "
            "It is not a real public tender."
        )
    else:
        source_url = document.get("source_url") or ""
        url_part = f" Full source: {source_url}" if source_url else ""
        st.info(
            f"This document is a manually curated public sample "
            f"(source: {document['source']}).{url_part}"
        )

    brief = database.get_brief_for_document(document["id"])

    st.subheader("Inspection brief")
    if brief is None:
        st.info("No brief stored for this document.")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Review domains", len(brief.risk_domains))
    m2.metric("Information gaps", len(brief.missing_info))
    m3.metric("Evidence snippets", len(brief.evidence))
    m4.metric("Confidence", brief.confidence)

    st.write(f"**Summary:** {brief.summary}")
    st.info(
        "Human review required - assistive output only; "
        "not a compliance or engineering decision."
    )

    st.markdown("**Detected technical scopes**")
    _bullets(brief.technical_scopes, "None detected")

    st.markdown("**Potential review domains**")
    _bullets(brief.risk_domains, "None detected")
    st.caption(
        "In this keyword placeholder, technical scopes and review domains are "
        "derived from the same keyword hits; they will diverge once a real "
        "extractor is added."
    )

    st.markdown("**Missing / unclear information**")
    _bullets(brief.missing_info, "None noted")

    st.markdown("**Suggested review questions**")
    _bullets(brief.review_questions, "None suggested")

    st.markdown("**Evidence snippets (source-traced)**")
    rows = evidence_rows(brief.evidence)
    if rows:
        st.dataframe(
            rows,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Matched term": st.column_config.TextColumn("Matched term", width="small"),
                "Location": st.column_config.TextColumn("Location", width="small"),
                "Snippet": st.column_config.TextColumn("Snippet", width="large"),
            },
        )
    else:
        st.markdown("*No evidence captured*")

    expander_label = (
        "Source document — synthetic sample"
        if is_synthetic
        else "Source document — public sample"
    )
    with st.expander(expander_label, expanded=False):
        st.write(f"**Source:** {document['source']}")
        url_display = document["source_url"] or ("n/a — offline synthetic sample" if is_synthetic else "n/a")
        st.write(f"**Source URL:** {url_display}")
        st.text(document["clean_text"])


if __name__ == "__main__":
    render()
