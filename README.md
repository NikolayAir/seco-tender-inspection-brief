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

## How to run

Run from the repository root (Windows / PowerShell):

```powershell
pip install -r requirements.txt
python -m src.pipeline                 # load synthetic sample -> SQLite -> placeholder brief
streamlit run src/app/streamlit_app.py # view the brief
pytest -q                              # smoke tests
```

The skeleton runs fully offline on bundled synthetic sample data; no network or API key is required.

## Limitations

This is an early skeleton. Extraction is a transparent keyword-based placeholder, not real AI/NLP, and the bundled document is synthetic sample data, not a real public tender. Full limitations to be added.