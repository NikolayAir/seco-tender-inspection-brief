# Decision Log

This file records key product and technical decisions made during the SECO take-home challenge. It is not a transcript of AI prompts or a time log. It summarizes decisions that affect the MVP scope, implementation choices, and interview-defensible trade-offs.

## 2026-06-01 — Product framing

Decision: Build "Tender-to-Inspection Brief", a small Building Intelligence MVP that turns public construction tender notices/documents into evidence-based technical-risk inspection briefs for a SECO-style technical reviewer.

Reasoning: SECO's work is centered on technical control, inspections, risk prevention, quality, safety, compliance awareness, and construction expertise. A reviewer-assistance workflow is more relevant than a generic construction chatbot or generic document summarizer.

Trade-off: The MVP will not make legal, regulatory, safety, compliance, or engineering decisions. It supports human technical review only. Generated findings should be tied to source evidence where possible.

## 2026-06-02 — UI stack

Decision: Use Streamlit for the MVP interface.

Reasoning: The challenge prioritizes a finished, reproducible MVP. Streamlit allows the Python data pipeline, SQLite storage, and inspection-brief output to be demonstrated quickly with minimal frontend overhead.

Trade-off: React is SECO's preferred production stack, but is left as a production migration step after the workflow, data model, and user value are validated.

## 2026-06-02 — Architecture scope

Decision: Start with a runnable local skeleton and then build a small vertical slice.

Reasoning: A working end-to-end path is safer than a broad but fragile architecture. The first useful path should be: sample public tender notice/document -> cleaned structured record -> SQLite storage -> evidence-based risk/inspection brief placeholder -> Streamlit display.

Trade-off: No Docker, React, FastAPI, LangChain, vector database, orchestration framework, cloud deployment, or multi-service architecture in the first version. This keeps the project reproducible and easier to explain, but it means production concerns such as scaling, authentication, monitoring, and scheduled ingestion remain out of scope.

## 2026-06-02 — Risk extraction scope

Decision: Keep the MVP usable with sample data and transparent rule-based extraction before considering any optional LLM/API dependency.

Reasoning: The app should run locally and remain reproducible without secrets, paid API keys, or network access. Rule-based extraction is less sophisticated than an LLM, but it makes the first version transparent, testable, and easier to validate.

Trade-off: Early extraction may miss nuanced risks and may produce simplistic classifications. This is acceptable for the first MVP because the goal is to demonstrate a defensible reviewer-assistance workflow, evidence traceability, and validation approach before adding a more sophisticated AI component.

## 2026-06-02 — Public data sample (hybrid approach)

Decision: Keep the synthetic sample for offline unit tests and add one manually curated real public procurement notice as a committed offline sample with full source provenance.

Reasoning: A real public notice adds credibility and demonstrates source traceability without requiring scraping or network access at runtime. The synthetic sample is preserved so all existing tests remain fully offline and deterministic. The public sample is committed as a static text file under `data/samples/`, with the `SOURCE_URL` pointing to the official Luxembourg Public Procurement Portal (PMP) consultation page.

Source: Luxembourg PMP consultation page (`https://pmp.b2g.etat.lu/entreprise/consultation/540151?orgAcronyme=t5y`). TED notice reference: 217578-2026. Buyer: Administration des bâtiments publics. Subject: asbestos remediation and selective deconstruction of the former CTIE building, Luxembourg. Short excerpt only; not a full tender dossier.

The notice was verified from the official PMP consultation page, not from a third-party aggregator. The source is labelled in the sample header as "Luxembourg Public Procurement Portal / TED-linked public notice"; the TED notice number is recorded as a reference. No strong license claims are made; the header carries a `REUSE_NOTE` pointing back to the source.

Trade-off: The public notice is in French. The current keyword extractor uses English terms, so it will not detect domains from this sample. The brief for this document will show no detected domains, which is documented as a known limitation rather than treated as a failure. Multilingual keyword support or an LLM-based extractor is a later step. The sample still exercises the full pipeline (load → clean → store → extract → store brief) with real provenance metadata, which is the goal of this step.
