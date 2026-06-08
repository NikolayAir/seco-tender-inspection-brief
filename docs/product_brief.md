# Tender-to-Inspection Brief

## User

A SECO-style technical reviewer or inspection coordinator preparing for an early review of a public construction or infrastructure project.

## Pain point

Public construction tender documents contain useful technical information, but they are slow to scan manually. A reviewer needs to quickly identify project scope, SECO-relevant technical review domains, missing information, and questions to check before inspection or design review.

## Product idea

The MVP turns public construction tender notices/documents into a structured, source-traced inspection-preparation brief.

It does not make legal, regulatory, safety, compliance, or engineering decisions. It supports human technical review only.

## Input

Public construction tender notices and selected public tender-document excerpts from Luxembourg/EU public procurement sources.

## Output

For each project, the tool provides:

* short project summary
* detected technical scopes
* SECO-relevant technical review domains
* missing or unclear information
* suggested technical review questions
* evidence snippets from the source text
* confidence / human-review flag

## SECO relevance

The product supports technical risk prevention, inspection preparation, quality review, safety/compliance awareness, and structured use of construction-sector documents.

## MVP scope delivered

* 3 bundled samples: 1 synthetic offline sample (deterministic test fixture) and 2 manually curated public Luxembourg PMP samples (CTIE: asbestos remediation and selective deconstruction; SNHBM Belvaux: building-services / heating, ventilation, electrical, kitchen works)
* local data pipeline
* SQLite database
* transparent rule-based domain-classification baseline with evidence traceability
* source traceability and evidence snippets
* simple Streamlit dashboard
* ad-hoc public-excerpt preview: pasted public text is processed in the current Streamlit session, rendered with the same source-traced brief format, and not stored by the app
* small manual validation sample (qualitative, 3 rows)

## Future dataset target

10-30 public construction/infrastructure examples from Luxembourg PMP / TED or equivalent public sources, replacing the current static bundled samples with a documented ingestion path.

## Out of scope for the current MVP

* final compliance judgment
* legal advice
* engineering decisions
* defect prediction
* computer vision
* internal SECO data
* URL ingestion, arbitrary website scraping, PDF/OCR, or LLM/RAG extraction
* persistent user uploads or saved ad-hoc pasted text
* production-grade scraping
* full React frontend
* replacement for construction document-management, BIM, site-inspection, defect-tracking, or project-management platforms
