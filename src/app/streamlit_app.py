"""Streamlit UI for the Tender-to-Inspection Brief MVP (read-only).

Run from the repository root:
    streamlit run src/app/streamlit_app.py

It reads the SQLite database produced by ``python -m src.pipeline`` and displays
stored documents and their baseline inspection briefs. Source labeling is
conditional: synthetic documents are flagged as offline test data; curated
public documents show the verified source URL.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
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
from src.pipeline import BUNDLED_SAMPLES, ingest_bundled_samples  # noqa: E402


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


VALIDATION_CSV_PATH = ROOT / "data" / "labels" / "manual_validation_v1.csv"


def load_validation_summary(csv_path: Path = VALIDATION_CSV_PATH) -> dict:
    """Summarize the committed qualitative manual-validation CSV (standard library only).

    Returns the number of manually reviewed samples and a mapping of
    ``match_status`` -> count. This is display-only transparency: it reads the
    existing ``data/labels/manual_validation_v1.csv`` and does not run, change, or
    re-evaluate the extraction logic.
    """
    with Path(csv_path).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    status_counts = Counter((row.get("match_status") or "").strip() for row in rows)
    return {
        "sample_count": len(rows),
        "status_counts": dict(status_counts),
    }


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


def render() -> None:
    """Render the read-only inspection-brief dashboard."""
    st.set_page_config(
        page_title="Tender-to-Inspection Brief", page_icon=":clipboard:", layout="wide"
    )

    st.title("Tender-to-Inspection Brief")
    st.caption(
        "Reviewer-assistance MVP for public construction notices and technical documents. "
        "Supports human technical review only. "
        "It does not make legal, regulatory, safety, compliance, or engineering decisions."
    )
    st.markdown(
        "**Demo coverage:** 3 bundled samples · 2 real public Luxembourg PMP excerpts · "
        "SQLite storage · source-traced rule-based domain-classification baseline · "
        "qualitative validation"
    )
    st.warning(
        "Prototype note: extraction uses a transparent rule-based "
        "domain-classification baseline. It is fully reproducible and source-traced, "
        "but it is not presented as a final NLP or LLM-based extraction system. "
        "Results are intended to help a reviewer identify possible technical review "
        "focus areas for human follow-up."
    )

    try:
        documents = _ensure_demo_data()
    except Exception:
        documents = []

    if not documents:
        st.error(
            "No documents found and automatic sample initialization failed. "
            "Run `python -m src.pipeline` from the repository root, then refresh."
        )
        st.stop()

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

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Review focus areas", len(brief.risk_domains))
    m2.metric("Baseline-detected gaps", len(brief.missing_info))
    m3.metric("Source evidence snippets", len(brief.evidence))
    m4.metric("Baseline confidence", brief.confidence)

    st.write(f"**Summary:** {brief.summary}")
    st.info(
        "Human review required - assistive output only; "
        "not a compliance or engineering decision."
    )

    st.markdown("**Detected technical scopes**")
    _bullets(brief.technical_scopes, "None detected")

    st.markdown("**Potential review focus areas**")
    _bullets(brief.risk_domains, "None detected by the baseline")
    st.caption(
        "Prototype limitation: in this rule-based domain-classification baseline, "
        "detected technical scopes and review focus areas are derived from the same "
        "keyword-to-domain taxonomy. In a stronger extraction model, these layers "
        "would be separated: scopes would describe what is present in the document, "
        "while review focus areas would indicate what a technical reviewer may need "
        "to check."
    )

    st.markdown("**Missing / unclear information**")
    _bullets(brief.missing_info, "None detected by the baseline")

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
                f"{status}: {count}"
                for status, count in sorted(summary["status_counts"].items())
                if status
            )
            st.write(f"**Manually reviewed samples:** {summary['sample_count']}")
            st.write(
                f"**Validation status counts:** {status_bits}"
                if status_bits
                else "**Validation status counts:** n/a"
            )
            st.caption(
                "This snapshot summarizes the committed manual validation set across all bundled "
                "samples, not only the currently selected document."
            )
            st.caption(
                "Qualitative validation only: each sample's expected review domains were "
                "compared by hand against the baseline output and recorded in "
                "`data/labels/manual_validation_v1.csv`."
            )
            st.caption(
                "No precision, recall, or F1 are reported, because the sample size is too "
                "small to support statistical accuracy claims."
            )
            st.caption(
                "Human technical review remains required; this snapshot supports human "
                "review only and is not a compliance or engineering judgement."
            )


if __name__ == "__main__":
    render()
