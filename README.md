# Tender-to-Inspection Brief

A small Building Intelligence MVP for turning public construction tender documents into evidence-based technical-risk inspection briefs.

## Problem

Public construction tender documents contain useful technical signals, but they are slow to scan manually. This tool helps a technical reviewer prepare a first-pass inspection brief.

## User

A technical inspection coordinator or reviewer preparing for early review of a construction or infrastructure project.

## SECO relevance

SECO works around technical control, inspections, risk prevention, safety, quality, compliance, and construction expertise. This MVP supports those workflows by structuring public project documents into review-oriented briefs.

## Current status

Work in progress.

## Planned MVP

* Data collection from public construction procurement sources
* Text extraction and cleaning
* SQLite storage
* AI-assisted or rule-based risk/domain extraction
* Evidence snippets and confidence
* Streamlit dashboard
* Manual validation sample

## Data sources

Two bundled samples are committed under `data/samples/`. Both are loaded by `python -m src.pipeline` with no network access required.

| File | Type | Source |
|---|---|---|
| `synthetic_sample_tender_001.txt` | Synthetic (hand-written) | Offline skeleton testing only; not a real tender |
| `public_lu_pmp_ctie_001.txt` | Manually curated public notice | Luxembourg Public Procurement Portal / TED-linked public notice. Buyer: Administration des bâtiments publics. TED notice ref: 217578-2026. Short excerpt only; full consultation at `SOURCE_URL` in the file header. |

The public sample is a short curated excerpt of a real Luxembourg public procurement consultation (asbestos remediation and selective deconstruction of the former CTIE building). It is included as a reproducible real-data example. No scraping was performed; the excerpt was manually curated from the official PMP consultation page.

The synthetic sample is retained as the default sample for offline unit tests.

## How to run

Run from the repository root (Windows / PowerShell):

```powershell
pip install -r requirements.txt
python -m src.pipeline                 # ingest all bundled samples -> SQLite -> placeholder briefs
streamlit run src/app/streamlit_app.py # view the briefs
pytest -q                              # smoke tests
```

Run a single sample file explicitly:

```powershell
python -m src.pipeline --sample data/samples/synthetic_sample_tender_001.txt
```

The project runs fully offline on the bundled sample data; no network access or API key is required.

## Limitations

- Extraction is a transparent keyword-based placeholder, not real AI/NLP.
- The keyword extractor uses English terms. The public Luxembourg PMP sample is in French; most keywords will not match it and the resulting brief will note no detected domains. Multilingual keyword support or an LLM extractor is a later step.
- The public sample is a short excerpt only; it does not represent the full tender dossier.
- Source traceability is at the document level; page- or paragraph-level evidence is not yet supported.
- Full limitations to be expanded as the MVP develops.
