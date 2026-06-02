"""Transparent keyword-based placeholder extractor.

This is NOT real AI/NLP. It is a small, explainable dictionary of keyword ->
review domain, scanned case-insensitively over the cleaned text. Each match
captures an evidence snippet (the line and the matched term) so every finding is
traceable to the source. It always returns confidence='low' and
human_review_required=True. It exists to prove the end-to-end wiring and the
evidence-traceability shape; a more capable extractor is a later step.
"""

from __future__ import annotations

from src.models import EvidenceSnippet, InspectionBrief, TenderDocument

# Each domain maps to the keywords that trigger it. Keywords are matched as
# lowercase substrings, so "electrical" also matches via "electric".
KEYWORD_DOMAINS: dict[str, list[str]] = {
    "Fire safety": ["fire"],
    "Electrical": ["electric"],
    "HVAC": ["hvac", "ventilation"],
    "Facade": ["facade", "façade", "cladding"],
    "Road / Infrastructure": ["road", "infrastructure", "bridge"],
    "Asbestos / hazardous materials": ["asbestos"],
    "Water / Sewer": ["water", "sewer", "drainage"],
}

# Generic review questions suggested per detected domain.
DOMAIN_QUESTIONS: dict[str, str] = {
    "Fire safety": "Is an up-to-date fire safety concept and detection design available for review?",
    "Electrical": "Are electrical installation specifications and compliance certificates provided?",
    "HVAC": "Are HVAC sizing, commissioning, and ventilation rate assumptions documented?",
    "Facade": "Are facade build-up, insulation, and fixing details specified for inspection?",
    "Road / Infrastructure": "Are road/infrastructure works scope and load assumptions defined?",
    "Asbestos / hazardous materials": "Is the asbestos survey report attached and a removal plan defined?",
    "Water / Sewer": "Are water supply and sewer/drainage connection details and capacities provided?",
}


def extract_brief(document: TenderDocument) -> InspectionBrief:
    """Run the keyword scan over the document and build an InspectionBrief."""
    text = document.clean_text
    lower_text = text.lower()
    lines = text.split("\n")

    detected: list[str] = []
    evidence: list[EvidenceSnippet] = []

    for domain, keywords in KEYWORD_DOMAINS.items():
        for keyword in keywords:
            if keyword in lower_text:
                detected.append(domain)
                snippet_line, line_no = _first_line_with(lines, keyword)
                evidence.append(
                    EvidenceSnippet(
                        snippet=snippet_line,
                        matched_term=keyword,
                        location=f"line {line_no}",
                    )
                )
                break  # one evidence snippet per domain is enough for the skeleton

    review_questions = [DOMAIN_QUESTIONS[d] for d in detected if d in DOMAIN_QUESTIONS]

    missing_info: list[str] = []
    if not detected:
        missing_info.append(
            "No known risk keywords detected in the sample; manual review needed."
        )

    summary = (
        f"'{document.title}'. Keyword placeholder detected "
        f"{len(detected)} potential review domain(s). "
        "Not AI-generated; for human technical review only."
    )

    return InspectionBrief(
        summary=summary,
        technical_scopes=detected,
        risk_domains=detected,
        missing_info=missing_info,
        review_questions=review_questions,
        evidence=evidence,
        confidence="low",
        human_review_required=True,
    )


def _first_line_with(lines: list[str], keyword: str) -> tuple[str, int]:
    """Return the first line containing the keyword and its 1-based line number."""
    for idx, line in enumerate(lines, start=1):
        if keyword in line.lower():
            return line.strip(), idx
    return "", 0
