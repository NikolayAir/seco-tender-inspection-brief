# Tender-to-Inspection Brief

## User

A SECO-style technical reviewer or inspection coordinator preparing for an early review of a public construction or infrastructure project.

## Pain point

Public construction tender documents contain useful technical information, but they are slow to scan manually. A reviewer needs to quickly identify project scope, likely technical-risk domains, missing information, and questions to check before inspection or design review.

## Product idea

The MVP turns public construction tender notices/documents into a structured inspection-preparation brief.

It does not make final compliance decisions. It supports human technical review.

## Input

Public construction tender notices and selected tender documents from Luxembourg/EU public procurement sources.

## Output

For each project:

* short project summary
* detected technical scopes
* likely SECO-relevant risk domains
* missing or unclear information
* suggested technical review questions
* evidence snippets from the source text
* confidence / human-review flag

## SECO relevance

The product supports technical risk prevention, inspection preparation, quality review, safety/compliance awareness, and structured use of construction-sector documents.

## MVP scope (delivered)

* 2 bundled samples: 1 synthetic offline sample (deterministic test fixture) and 1 manually curated public Luxembourg PMP/TED-linked sample (asbestos remediation and selective deconstruction, CTIE building)
* local data pipeline
* SQLite database
* transparent rule-based structured extraction with evidence traceability
* source traceability and evidence snippets
* simple Streamlit dashboard
* small manual validation sample (qualitative, 2 rows)

## Future dataset target

* 10-30 public construction/infrastructure examples from Luxembourg PMP / TED or equivalent public sources, replacing the current static bundled samples with a documented ingestion path

## Out of scope

* final compliance judgment
* legal advice
* engineering decisions
* defect prediction
* computer vision
* internal SECO data
* production-grade scraping
* full React frontend