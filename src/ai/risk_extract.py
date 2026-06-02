"""Transparent keyword-based placeholder extractor.

This is NOT real AI/NLP. It is a small, explainable dictionary of keyword ->
review domain, scanned case-insensitively over the cleaned text. Each match
captures an evidence snippet (the line and the matched term) so every finding is
traceable to the source. It always returns confidence='low' and
human_review_required=True. It exists to prove the end-to-end wiring and the
evidence-traceability shape; a more capable extractor is a later step.

The keyword dictionary includes a small set of French construction terms added
specifically for the curated Luxembourg PMP/CTIE sample. This is NOT general
multilingual support or French-language NLP; it is a targeted extension for one
manually curated real-data sample to demonstrate source-traced findings on a
real public notice. False positives are possible on other French documents.
"""

from __future__ import annotations

from src.models import EvidenceSnippet, InspectionBrief, TenderDocument

# Each domain maps to the keywords that trigger it. Keywords are matched as
# lowercase substrings, so "electrical" also matches via "electric".
# French terms are marked with (FR) and were added specifically for the curated
# Luxembourg PMP/CTIE sample; they are not general multilingual NLP.
KEYWORD_DOMAINS: dict[str, list[str]] = {
    "Fire safety": ["fire"],
    "Electrical": ["electric"],
    "HVAC": ["hvac", "ventilation"],
    "Facade": ["facade", "façade", "cladding"],
    "Road / Infrastructure": ["road", "infrastructure", "bridge"],
    "Asbestos / hazardous materials": [
        "asbestos",
        "amiant",   # (FR) amiantées / désamiantage
        "flocage",  # (FR) flocage FMA (sprayed asbestos insulation)
    ],
    "Water / Sewer": ["water", "sewer", "drainage"],
    # Domains added for French-language construction/deconstruction content:
    "Structure / deconstruction": [
        "déconstruct",  # (FR) déconstruction
        "démoli",       # (FR) démolition / démolir
        "dalles",       # (FR) structural slabs
        "charpente",    # (FR) structural framework / metal framework
    ],
    "Remediation / site preparation": [
        "curage",           # (FR) internal stripping / site clearing
        "assainissement",   # (FR) remediation / sanitation works
    ],
    "Materials reuse / circularity": [
        "réemploi",     # (FR) reuse; matches réemployables
        "valorisation", # (FR) recovery / value recovery of materials
    ],
}

# Phrases that often signal missing or unclear information in a tender notice.
# Matched case-insensitively over whitespace-flattened text (see _scan_missing_info).
MISSING_INFO_PHRASES: list[str] = [
    "not attached",
    "not included",
    "must be requested separately",
    "referenced but",
]

# Generic review questions suggested per detected domain.
DOMAIN_QUESTIONS: dict[str, str] = {
    "Fire safety": "Is an up-to-date fire safety concept and detection design available for review?",
    "Electrical": "Are electrical installation specifications and compliance certificates provided?",
    "HVAC": "Are HVAC sizing, commissioning, and ventilation rate assumptions documented?",
    "Facade": "Are facade build-up, insulation, and fixing details specified for inspection?",
    "Road / Infrastructure": "Are road/infrastructure works scope and load assumptions defined?",
    "Asbestos / hazardous materials": "Is the asbestos survey report attached and a removal plan defined?",
    "Water / Sewer": "Are water supply and sewer/drainage connection details and capacities provided?",
    "Structure / deconstruction": (
        "Are structural integrity assessments and a phased deconstruction/demolition "
        "plan available for review?"
    ),
    "Remediation / site preparation": (
        "Is a site remediation plan including scope, methodology, and waste disposal documented?"
    ),
    "Materials reuse / circularity": (
        "Is a materials reuse and recovery plan specified, "
        "and are quantities and destinations identified?"
    ),
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

    missing_info, missing_evidence = _scan_missing_info(text)
    evidence.extend(missing_evidence)
    if not detected and not missing_info:
        missing_info.append(
            "No known risk keywords or information gaps detected; manual review needed."
        )

    summary = (
        f'For "{document.title}", the rule-based extractor flagged '
        f"{len(detected)} possible technical review focus area(s) and "
        f"{len(missing_info)} explicit information gap(s). "
        "The output is derived from transparent keyword rules, not from an LLM, "
        "and is intended for human technical review only."
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


def _scan_missing_info(text: str) -> tuple[list[str], list[EvidenceSnippet]]:
    """Find sentences signalling missing/unclear information.

    Whitespace (including newlines) is flattened first, because tender text often
    wraps a phrase like "not included" across two lines. Each gap sentence is
    reported once, with the matched phrase as the traceable term. Location is
    "source text" rather than a line number because of this flattening.
    """
    flat = " ".join(text.split())
    sentences = [s.strip() for s in flat.split(".") if s.strip()]

    notes: list[str] = []
    evidence: list[EvidenceSnippet] = []
    seen: set[str] = set()

    for phrase in MISSING_INFO_PHRASES:
        for sentence in sentences:
            if phrase in sentence.lower() and sentence not in seen:
                seen.add(sentence)
                note = f"{sentence}."
                notes.append(note)
                evidence.append(
                    EvidenceSnippet(
                        snippet=note,
                        matched_term=phrase,
                        location="source text",
                    )
                )
                break

    return notes, evidence
