"""Streamlit UI for the Tender-to-Inspection Brief skeleton (read-only).

Run from the repository root:
    streamlit run src/app/streamlit_app.py

It reads the SQLite database produced by ``python -m src.pipeline`` and displays
the stored synthetic document and its keyword-placeholder inspection brief.
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

from src.db import database  # noqa: E402


def render() -> None:
    """Render the read-only inspection-brief dashboard."""
    st.set_page_config(page_title="Tender-to-Inspection Brief", layout="wide")

    st.title("Tender-to-Inspection Brief")
    st.caption(
        "Reviewer-assistance MVP - supports human technical review only. "
        "It does not make legal, regulatory, safety, compliance, or engineering decisions."
    )
    st.warning(
        "Skeleton build: extraction is a transparent keyword-based placeholder (not real AI/NLP), "
        "and the loaded document is synthetic sample data for offline testing, not a real public tender."
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

    brief = database.get_brief_for_document(document["id"])

    left, right = st.columns(2)

    with left:
        st.subheader("Source document")
        st.write(f"**Source:** {document['source']}")
        st.write(f"**Source URL:** {document['source_url'] or 'n/a (offline synthetic sample)'}")
        with st.expander("Cleaned text"):
            st.text(document["clean_text"])

    with right:
        st.subheader("Inspection brief (placeholder)")
        if brief is None:
            st.info("No brief stored for this document.")
            return
        st.write(f"**Summary:** {brief.summary}")
        st.write(f"**Confidence:** {brief.confidence}")
        st.write(f"**Human review required:** {brief.human_review_required}")

        st.markdown("**Detected technical scopes**")
        st.write(brief.technical_scopes or "None detected")

        st.markdown("**Potential review domains**")
        st.write(brief.risk_domains or "None detected")

        st.markdown("**Missing / unclear information**")
        st.write(brief.missing_info or "None noted")

        st.markdown("**Suggested review questions**")
        for question in brief.review_questions:
            st.write(f"- {question}")

        st.markdown("**Evidence snippets (source-traced)**")
        for ev in brief.evidence:
            st.write(f"- [{ev.location}] matched '{ev.matched_term}': \"{ev.snippet}\"")


if __name__ == "__main__":
    render()
