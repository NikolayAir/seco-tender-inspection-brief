# Decision Log

This file records key product and technical decisions made during the SECO take-home challenge. It is not a transcript of AI prompts or a time log. It summarizes decisions that affect the MVP scope, implementation choices, and interview-defensible trade-offs.

## 2026-06-01/02 — Product framing

Decision: Build "Tender-to-Inspection Brief", a small Building Intelligence MVP that turns public construction tender notices/documents into evidence-based technical-risk inspection briefs.

Reasoning: SECO's work is centered on technical control, inspections, risk prevention, quality, safety, compliance awareness, and construction expertise. A reviewer-assistance workflow is more relevant than a generic construction chatbot.

Trade-off: The MVP will not make legal, regulatory, safety, compliance, or engineering decisions. It supports human technical review only.

## 2026-06-02 — UI stack

Decision: Use Streamlit for the MVP interface.

Reasoning: The challenge prioritizes a finished, reproducible MVP. Streamlit allows the Python data pipeline, SQLite storage, and inspection-brief output to be demonstrated quickly.

Trade-off: React is SECO's preferred production stack, but is left as a production migration step after the workflow and data model are validated.

## 2026-06-02 — Architecture scope

Decision: Start with a runnable local skeleton and then build a small vertical slice.

Reasoning: A working end-to-end path is safer than a broad but fragile architecture.

Trade-off: No Docker, React, FastAPI, LangChain, vector database, orchestration framework, or cloud deployment in the first version.

## 2026-06-02 — AI/risk extraction scope

Decision: Keep the MVP usable with sample data and/or rule-based placeholder extraction before adding any LLM/API dependency.

Reasoning: The app should run locally and remain reproducible without secrets or paid API keys.

Trade-off: Early extraction may be less sophisticated, but it is transparent, testable, and easier to validate.