"""Streamlit interface for the Tender-to-Inspection Brief application.

Run from the repository root:
    streamlit run src/app/streamlit_app.py

The interface displays persisted review briefs for bundled samples and supports
session-only analysis of pasted public excerpts. Synthetic documents are
identified as offline test data; curated public documents show their verified
source URL.
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

from src.ai.risk_extract import (  # noqa: E402
    KEYWORD_DOMAINS,
    MISSING_INFO_PHRASES,
    extract_brief,
)
from src.collect.sample_loader import build_document_from_text  # noqa: E402
from src.db import database  # noqa: E402
from src.exports import serialize_brief_export  # noqa: E402
from src.models import EvidenceSnippet  # noqa: E402
from src.pipeline import BUNDLED_SAMPLES, ingest_bundled_samples  # noqa: E402
from src.validation.manual_validation import (  # noqa: E402
    humanize_validation_label,
    load_validation_summary,
)

# Upper bound on ad-hoc pasted text, to keep the in-session preview responsive.
MAX_ADHOC_CHARS = 50_000


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


def adhoc_input_error(text: str, max_chars: int = MAX_ADHOC_CHARS) -> str | None:
    """Validate ad-hoc pasted text; return a user-facing message, or None if OK.

    Pure (non-UI) so it can be unit-tested: empty/whitespace input and over-length
    input are rejected; valid input returns None.
    """
    if not text or not text.strip():
        return "Please paste a public tender or document excerpt to preview."
    if len(text) > max_chars:
        return (
            f"Excerpt is too long ({len(text):,} characters). "
            f"Please paste at most {max_chars:,} characters."
        )
    return None


def brief_export_filename(document_id: int) -> str:
    """Return the deterministic filename used for one persisted brief export."""
    return f"inspection-brief-document-{document_id}.json"


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


def render_brief_body(brief) -> None:
    """Render the shared review-brief body for bundled and ad-hoc sources.

    Source provenance and the validation snapshot remain in the calling view
    because they depend on how the brief was created.
    """
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Review focus areas", len(brief.risk_domains))
    m2.metric("Detected information gaps", len(brief.missing_info))
    m3.metric("Evidence snippets", len(brief.evidence))
    m4.metric("Extraction confidence", brief.confidence)

    st.write(f"**Summary:** {brief.summary}")
    st.info(
        "Human review required. Verify the findings against the source "
        "evidence before acting on them."
    )

    st.markdown("**Detected technical scopes**")
    _bullets(brief.technical_scopes, "None detected")

    st.markdown("**Potential review focus areas**")
    _bullets(brief.risk_domains, "None detected by the baseline")
    st.caption(
        "Current limitation: technical scopes and review focus areas use the "
        "same domain taxonomy, so the two sections may overlap."
    )

    st.markdown("**Missing / unclear information**")
    _bullets(brief.missing_info, "None detected")

    st.markdown("**Suggested review questions**")
    _bullets(brief.review_questions, "None suggested")

    st.markdown("**Evidence snippets (source-traced)**")
    rows = evidence_rows(brief.evidence)
    if rows:
        st.dataframe(
            rows,
            hide_index=True,
            width="stretch",
            column_config={
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Matched term": st.column_config.TextColumn(
                    "Matched term", width="small"
                ),
                "Location": st.column_config.TextColumn("Location", width="small"),
                "Snippet": st.column_config.TextColumn("Snippet", width="large"),
            },
        )
    else:
        st.markdown("*No evidence captured*")


def _ensure_demo_data() -> list[dict]:
    """Return stored documents, initializing bundled samples when needed.

    Supports hosted demos (e.g. Streamlit Community Cloud) where the app is opened
    directly from this file without first running ``python -m src.pipeline``. Runs
    fully offline against the committed bundled samples; it does not change the
    schema, extractor logic, or sample provenance. The explicit pipeline command
    remains the recommended local reproducibility check.
    """
    database.init_db()
    documents = database.get_documents()
    if len(documents) >= len(BUNDLED_SAMPLES):
        return documents

    ingest_bundled_samples()
    documents = database.get_documents()
    if len(documents) < len(BUNDLED_SAMPLES):
        raise RuntimeError(
            f"Expected {len(BUNDLED_SAMPLES)} bundled documents, "
            f"found {len(documents)} after initialization."
        )
    return documents


def render_bundled_view() -> None:
    """Render persisted review briefs for bundled samples."""
    try:
        documents = _ensure_demo_data()
    except Exception:
        documents = []

    if not documents:
        st.error(
            "No documents found and automatic sample initialization failed. "
            "Run `python -m src.pipeline` from the repository root, then refresh."
        )
        return

    labels = {f"#{d['id']} - {d['title']}": d for d in documents}
    choice = st.selectbox("Select a document", list(labels.keys()))
    document = labels[choice]

    is_synthetic = document["source"] == "synthetic_sample"
    if is_synthetic:
        st.info(
            "This document is synthetic sample data for offline testing. "
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

    export_payload = database.get_latest_brief_export(document["id"])
    if export_payload is not None:
        st.download_button(
            "Download review brief (JSON)",
            data=serialize_brief_export(export_payload),
            file_name=brief_export_filename(document["id"]),
            mime="application/json",
            help=(
                "Includes the review brief, source evidence, document metadata, "
                "processing provenance, and version information."
            ),
        )

    render_brief_body(brief)

    expander_label = (
        "Source document — synthetic sample"
        if is_synthetic
        else "Source document — public sample"
    )
    with st.expander(expander_label, expanded=False):
        st.write(f"**Source:** {document['source']}")
        url_display = document["source_url"] or (
            "n/a — offline synthetic sample" if is_synthetic else "n/a"
        )
        st.write(f"**Source URL:** {url_display}")
        st.text(document["clean_text"])

    with st.expander("Validation snapshot", expanded=False):
        try:
            summary = load_validation_summary()
        except Exception:
            st.caption("Validation summary is currently unavailable.")
        else:
            status_bits = ", ".join(
                f"{humanize_validation_label(status)} ({count})"
                for status, count in sorted(summary["status_counts"].items())
                if status
            )
            st.write(f"**Manually reviewed samples:** {summary['sample_count']}")
            st.write(
                f"**Validation outcomes:** {status_bits}"
                if status_bits
                else "**Validation outcomes:** n/a"
            )
            detail_rows = summary.get("detail_rows", [])
            if detail_rows:
                st.dataframe(
                    detail_rows,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "sample_id": st.column_config.TextColumn("Sample", width="small"),
                        "source_type": st.column_config.TextColumn(
                            "Source type", width="small"
                        ),
                        "match_status": st.column_config.TextColumn("Match", width="small"),
                        "manually_expected_domains": st.column_config.TextColumn(
                            "Manually expected domains", width="large"
                        ),
                        "extracted_domains": st.column_config.TextColumn(
                            "Extracted domains", width="large"
                        ),
                    },
                )
            st.caption(
                "Qualitative validation across all bundled samples: expected and "
                "extracted review domains were compared manually. The dataset is "
                "too small for statistical accuracy claims. Detailed notes are "
                "stored in `data/labels/manual_validation_v1.csv`."
            )


def render_adhoc_view() -> None:
    """Render session-only analysis for a pasted public excerpt."""
    st.info(
        "Paste public, non-confidential text to generate a review brief. "
        "The excerpt is processed only in the current session and is not stored."
    )

    title = st.text_input(
        "Document title (optional)",
        help="Used only if the pasted text does not contain a TITLE: line.",
    )
    source_url = st.text_input("Source URL (optional)")
    text = st.text_area(
        "Paste a public tender or technical document excerpt",
        height=240,
        help="Public, non-confidential text only.",
    )

    if not st.button("Generate review brief"):
        return

    error = adhoc_input_error(text)
    if error:
        st.warning(error)
        return

    document = build_document_from_text(
        text,
        source_url=source_url.strip(),
        default_title=title.strip() or "Ad-hoc public excerpt",
    )
    brief = extract_brief(document)

    st.subheader("Review brief preview")
    render_brief_body(brief)
    st.caption(
        "This preview is not stored. Validation results for bundled samples "
        "do not apply to pasted excerpts."
    )


def render() -> None:
    """Render bundled review briefs and the public-excerpt analysis view."""
    st.set_page_config(
        page_title="Tender-to-Inspection Brief", page_icon=":clipboard:", layout="wide"
    )

    st.title("Tender-to-Inspection Brief")
    st.caption(
        "Turns public construction notices and technical documents into "
        "source-traced review briefs for human technical review."
    )
    st.markdown(
        "**Current coverage:** 3 bundled samples · "
        "2 public Luxembourg procurement excerpts · SQLite persistence · "
        "transparent rule-based extraction · qualitative validation"
    )
    st.warning(
        "Review the suggested focus areas against the linked source evidence. "
        "The application supports technical review but does not make legal, "
        "regulatory, compliance, safety, or engineering decisions."
    )

    tab_bundled, tab_adhoc = st.tabs(["Bundled samples", "Analyze public excerpt"])
    with tab_bundled:
        render_bundled_view()
    with tab_adhoc:
        render_adhoc_view()


if __name__ == "__main__":
    render()
