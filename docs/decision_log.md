# Decision Log

This file summarizes selected product and technical decisions that shaped the MVP scope, implementation choices, validation approach, and product trade-offs.

## 2026-06-01 — Product framing

Decision: Build "Tender-to-Inspection Brief", a focused reviewer-assistance MVP that turns public construction tender notices and excerpts into structured, source-traced technical review briefs.

Reasoning: A reviewer-assistance workflow provides a clearer and more testable product boundary than a generic construction chatbot or document summarizer. The application should surface technical domains, missing information, source evidence, and review questions while leaving final judgment with the reviewer.

Trade-off: The MVP will not make legal, regulatory, safety, compliance, or engineering decisions. It supports human technical review only. Generated findings should be tied to source evidence where possible.

## 2026-06-02 — UI stack

Decision: Use Streamlit for the MVP interface.

Reasoning: Streamlit allows the Python pipeline, SQLite storage, and inspection-brief output to be demonstrated through a small, reproducible interface with minimal frontend overhead.

Trade-off: Streamlit is suitable for the current single-user demonstration, but a separate frontend should only be introduced when it materially improves the reviewer workflow and can be supported with feature parity, tests, and a clear deployment path.

## 2026-06-02 — Architecture scope

Decision: Start with a runnable local skeleton and then build a small vertical slice.

Reasoning: A working end-to-end path is safer than a broad but fragile architecture. The first useful path should be: sample public tender notice/document -> cleaned structured record -> SQLite storage -> evidence-based risk/inspection brief -> Streamlit display.

Trade-off: No Docker, React, FastAPI, LangChain, vector database, orchestration framework, cloud deployment, or multi-service architecture in the first version. This keeps the project reproducible and easier to explain, but it means production concerns such as scaling, authentication, monitoring, and scheduled ingestion remain out of scope.

## 2026-06-02 — Risk extraction scope

Decision: Keep the MVP usable with sample data and transparent rule-based extraction before considering any optional LLM/API dependency.

Reasoning: The app should run locally and remain reproducible without secrets, paid API keys, or network access. Rule-based extraction is less sophisticated than an LLM, but it makes the first version transparent, testable, and easier to validate.

Trade-off: Early extraction may miss nuanced risks and may produce simplistic classifications. This is acceptable for the first MVP because the goal is to demonstrate a defensible reviewer-assistance workflow, evidence traceability, and validation approach before adding a more sophisticated extraction component.

## 2026-06-02 — Public data sample (hybrid approach)

Decision: Keep the synthetic sample for offline unit tests and add one manually curated real public procurement notice as a committed offline sample with full source provenance.

Reasoning: A real public notice adds credibility and demonstrates source traceability without requiring scraping or network access at runtime. The synthetic sample is preserved so all existing tests remain fully offline and deterministic. The public sample is committed as a static text file under `data/samples/`, with the `SOURCE_URL` pointing to the official Luxembourg Public Procurement Portal (PMP) consultation page.

Source: Luxembourg PMP consultation page (`https://pmp.b2g.etat.lu/entreprise/consultation/540151?orgAcronyme=t5y`). TED notice reference: 217578-2026. Buyer: Administration des bâtiments publics. Subject: asbestos remediation and selective deconstruction of the former CTIE building, Luxembourg. Short excerpt only; not a full tender dossier.

The notice was verified from the official PMP consultation page, not from a third-party aggregator. The source is labelled in the sample header as "Luxembourg Public Procurement Portal / TED-linked public notice"; the TED notice number is recorded as a reference. No strong license claims are made; the header carries a `REUSE_NOTE` pointing back to the source.

Trade-off: The public notice is in French. The MVP includes a small targeted French keyword extension for the CTIE sample so that the public sample produces source-traced findings, but this is not general French NLP or multilingual extraction. French missing-information signals and broader French construction terminology remain out of scope. The sample exercises the full pipeline (load -> clean -> store -> extract -> store brief) with real provenance metadata while keeping runtime fully offline.

## 2026-06-02 — French keyword extension

Decision: Add a small set of French construction keywords for the curated CTIE/PMP sample.

Reasoning: The real public sample is in French and should demonstrate evidence traceability rather than appearing empty in the demo. A targeted dictionary extension keeps the rule-based extractor transparent, testable, and easy to explain.

Trade-off: This is not general multilingual NLP. It improves coverage for the curated CTIE sample but can miss paraphrases, other French technical terms, and French-language missing-information signals. It is a controlled MVP extension, not a production extraction strategy.

## 2026-06-02 — Manual validation sample

Decision: Add a small qualitative manual validation CSV at `data/labels/manual_validation_v1.csv`, with a companion regression test at `tests/test_validation.py`.

Reasoning: A transparent qualitative review of extractor output is more honest than omitting validation or reporting spurious metrics on a rule-based baseline. The file records manually expected domains, the extractor's actual output, a match status, taxonomy gaps, and known limitations for each sample.

Trade-off: The validation sample is small and qualitative; no precision, recall, or F1 figures are reported or implied. Match status (`match`) reflects agreement with the domains declared in this validation file only, not against an exhaustive or independent gold standard. Structural, energy, waste-disposal, site-logistics, and French missing-information signals are documented as out-of-taxonomy gaps rather than counted as quantified false negatives. The regression test guards against silent extractor regressions; it does not evaluate correctness against an independent standard.

## 2026-06-03 — Second public sample (building services, SNHBM Belvaux)

Decision: Add one more manually curated real public Luxembourg PMP sample (`public_lu_pmp_snhbm_belvaux_001.txt`) covering a different technical scope — building services: heating, ventilation, electrical, and kitchen works — and a small targeted French keyword extension (`chauffage`, `électric`, `cuisine`) plus one narrow new domain, "Kitchen / catering installations".

Source: Luxembourg PMP consultation page (`https://pmp.b2g.etat.lu/entreprise/consultation/542824?orgAcronyme=t5y`). Reference: 2601359. Buyer: SNHBM - Société Nationale des Habitations à Bon Marché. Subject: heating, ventilation, electricity and kitchen works for commercial and office spaces in Belvaux. Short curated excerpt only; the tender dossier was not downloaded or committed.

Reasoning: The first public sample (CTIE) only exercised the asbestos/deconstruction scope. A second real public notice with a distinct building-services scope broadens real-public-data coverage and tests that the source-traced reviewer-assistance workflow and the French keyword extension generalise across more than one technical scope. Existing HVAC and Electrical domains are reused; only "cuisine" required a new narrow domain.

Trade-off: This keeps the MVP fully offline and reproducible, but it remains a short curated excerpt rather than production ingestion, and the kitchen domain is a narrow reviewer-assistance signal, not a safety or compliance classification. The French keyword additions are a small targeted extension, not general multilingual NLP. Validation stays qualitative: one new `match` row is added to the validation CSV and guarded by the regression test; no precision, recall, or F1 figures are reported.

## 2026-06-03 — Hosted demo readiness

Decision: Deploy-readiness was added for the Streamlit demo by allowing the app to initialize the bundled offline samples automatically when the local SQLite database is missing or empty.

Reasoning: The local reproducibility path remains explicit (`python -m src.pipeline` before opening the app), but a hosted Streamlit demo should open directly for a reviewer without requiring a manual pipeline command. The app still uses only committed bundled samples, runs fully offline, and does not require API keys, secrets, scraping, or network access.

Trade-off: This is a convenience layer for the hosted demo, not production ingestion. The generated SQLite database remains local/generated data and is not committed. For production, ingestion would need a documented source connector, operational monitoring, authentication, audit logging, and a managed database.

## 2026-06-03 — Evidence snippet selection

Decision: The rule-based extraction baseline was updated to prefer non-title source lines for evidence snippets when a detected domain appears both in the title and later in the document body.

Reasoning: A title line can be valid evidence, but body or object lines usually provide more useful technical context for a reviewer. For example, the SNHBM Belvaux sample contains heating, ventilation, electrical, and kitchen signals in both the title and object text; using the object line gives a clearer source trace without changing the detected domains.

Trade-off: Evidence remains line-level and keyword-based. This is not semantic ranking, section parsing, or NLP. If no non-title line is available, the title line remains a valid fallback. Detected domains, review questions, confidence, and human-review flags are unchanged.

## 2026-06-07 — Ad-hoc public-excerpt preview

Decision: Add an ephemeral Streamlit mode for pasted public tender/document excerpts. The preview builds an in-memory document from pasted text, uses the existing cleaning and rule-based extraction path, and renders the same source-traced inspection-brief format as the bundled samples.

Reasoning: The portfolio demo is more useful when a reviewer can try a short public excerpt directly, while the implementation remains small, offline, reproducible, and grounded in the existing validated workflow. Reusing the current extractor and brief renderer avoids adding a second product path.

Trade-off: This is a preview mode, not production ingestion. Pasted text is processed in the current Streamlit session and is not stored in SQLite by the app. No URL fetching, scraping, PDF/OCR, LLM/API call, authentication, database schema change, or new dependency is introduced. Arbitrary pasted text is not covered by the bundled manual validation set, so human technical review remains required.
