# Decision Log

This log records selected product and technical decisions that have shaped the application, including its scope, architecture, data strategy, validation approach, provenance model, and compatibility boundaries.

New entries are added only when a decision materially affects one of those areas. Superseded decisions should remain in the log with a reference to the later decision that replaced them.

## 2026-06-01 — Product framing

Decision: Build Tender-to-Inspection Brief as a focused reviewer-assistance application that turns public construction tender notices and excerpts into structured, source-traced technical review briefs.

Reasoning: A defined reviewer workflow is clearer and more testable than a generic construction chatbot or document summarizer. The application should surface technical domains, information gaps, source evidence, and review questions while leaving interpretation and follow-up decisions with the reviewer.

Trade-off: The application does not make legal, regulatory, safety, compliance, or engineering decisions. Human technical review remains required.

## 2026-06-02 — UI stack

Decision: Use Streamlit for the current application interface.

Reasoning: Streamlit provides a small reproducible interface around the Python pipeline, SQLite persistence, and structured review output without requiring a separate frontend service.

Trade-off: Streamlit suits the current single-user workflow. A separate frontend should only be introduced when it materially improves reviewer workflows and can be supported with feature parity, tests, and a clear deployment path.

## 2026-06-02 — Architecture scope

Decision: Start with a runnable local vertical slice: bundled source document → normalized record → SQLite persistence → source-traced review brief → Streamlit display.

Reasoning: A complete end-to-end path provides more value and is easier to validate than a broad but partially implemented architecture.

Trade-off: Multi-service deployment, authentication, monitoring, scheduled ingestion, and scaling concerns are deferred until concrete requirements justify them.

## 2026-06-02 — Extraction baseline

Decision: Use transparent rule-based extraction before considering an optional model or external API dependency.

Reasoning: The application should run locally without secrets, paid services, or network access. A deterministic baseline is limited but reproducible, testable, and straightforward to validate.

Trade-off: Keyword-based extraction can miss nuanced or paraphrased signals and cannot provide general semantic understanding. Any later extraction method should be evaluated against the documented baseline and preserve structured output, evidence traceability, versioning, and human review.

## 2026-06-02 — Hybrid sample strategy

Decision: Retain a synthetic sample for deterministic tests and add a manually curated public procurement excerpt with explicit source provenance.

Reasoning: A real public notice demonstrates the workflow on realistic material without introducing scraping or runtime network dependencies. The synthetic sample remains a stable offline fixture.

The first public sample is based on the Luxembourg Public Procurement Portal notice for asbestos remediation and selective deconstruction of the former CTIE building. Its committed header records the official source URL and TED reference `217578-2026`.

Trade-off: The committed data is a short curated French excerpt rather than a complete tender dossier or automated ingestion source. Its targeted language coverage should not be interpreted as general French-language extraction.

## 2026-06-02 — Targeted French terminology

Decision: Add a small set of French construction terms required by the curated CTIE sample.

Reasoning: The public sample should produce meaningful source-traced findings while keeping the extraction taxonomy transparent and testable.

Trade-off: The added terms cover a narrow set of known examples. French paraphrases, broader construction terminology, and French-language information-gap signals can still be missed.

## 2026-06-02 — Qualitative validation

Decision: Add a manually reviewed validation file at `data/labels/manual_validation_v1.csv` and guard it with `tests/test_validation.py`.

Reasoning: Recording expected domains, actual output, taxonomy gaps, and known limitations provides a transparent regression baseline. This is more defensible than omitting validation or reporting unsupported quantitative metrics.

Trade-off: The validation set is small and qualitative. A `match` records agreement with the declared expectations in the file, not correctness against an exhaustive independent gold standard. Precision, recall, and F1 are therefore not reported.

## 2026-06-03 — Second public sample

Decision: Add `public_lu_pmp_snhbm_belvaux_001.txt`, covering heating, ventilation, electrical, and kitchen works, together with a small terminology extension and the narrow domain `Kitchen / catering installations`.

Reasoning: A second public notice exercises the workflow on a different technical scope and tests whether the source-traced extraction path generalizes beyond the initial asbestos and deconstruction example.

The sample is based on Luxembourg PMP reference `2601359`; its official source metadata is recorded in the committed file header.

Trade-off: The sample remains a curated excerpt, and the new terminology and kitchen domain represent narrow reviewer-assistance signals rather than general multilingual or compliance classification.

## 2026-06-03 — Hosted application initialization

Decision: Allow the Streamlit application to initialize the bundled samples automatically when the generated SQLite database is absent or incomplete.

Reasoning: The explicit local path remains `python -m src.pipeline`, but the hosted application should open with usable bundled content without requiring a manual initialization command.

Trade-off: Automatic initialization is a convenience for the bundled workflow, not a production ingestion mechanism. The generated database remains local runtime data and is not committed.

## 2026-06-03 — Evidence snippet selection

Decision: Prefer non-title source lines when a detected domain appears in both the document title and body.

Reasoning: Body lines usually provide more useful technical context while preserving the same detected domain and source traceability.

Trade-off: Evidence selection remains keyword-based and line-level rather than semantic ranking or section-aware parsing. The title remains a fallback when no suitable body line exists.

## 2026-06-07 — Public-excerpt preview

Decision: Add an ephemeral Streamlit path for pasted public tender or document excerpts. It reuses the existing cleaning, extraction, and brief-rendering workflow.

Reasoning: Allowing a reviewer to try a short public excerpt makes the application more useful without creating a separate processing path or introducing external services.

Trade-off: Pasted text is processed only in the current session and is not persisted. The path does not fetch URLs, scrape websites, parse PDFs, or call an external model or API. Arbitrary pasted excerpts are outside the bundled validation set.

## 2026-07-31 — Processing-run provenance

Decision: Persist a processing-run record for every stored inspection brief. Each run records the source document, UTC timestamp, extractor name and version, brief schema version, and SHA-256 fingerprint of the normalized source text.

Reasoning: Replacing the previous brief on every execution preserved only the latest result and removed information needed to identify how a stored brief was produced. Linking each brief to an explicit run preserves processing history while keeping the current interface focused on the latest result.

Trade-off: The `documents` table still represents the current content of each logical document rather than complete source-revision history. Existing databases are upgraded additively, and historical briefs receive explicit legacy provenance because their original versions were not recorded. Browsing and comparing previous runs remains future work.

## 2026-08-03 — Versioned persisted-brief JSON export

Decision: Define a `1.0.0` JSON export envelope for one persisted inspection brief and expose it as a download for bundled samples. The envelope contains document metadata, the exact linked processing run, extractor and brief-schema versions, the normalized-source fingerprint, the stored brief identifier, and the complete structured brief with evidence.

Reasoning: A persisted result should be transferable outside the application without losing the metadata needed to identify how it was produced. Keeping export schema, brief schema, and extractor versions separate makes compatibility decisions explicit. Deterministic serialization provides a stable representation of the same persisted payload for later verification work.

Trade-off: The export represents the latest persisted brief for one logical document, not a database dump or source-document archive. Run-specific identifiers and timestamps are retained, so exports from separate processing runs are not expected to be byte-identical. Earlier source-text revisions are not preserved, and incompatible future contract changes require an explicit export-version decision. The pasted-text path remains unpersisted and is not downloadable through this workflow.

## 2026-08-03 — Independent-run reproducibility boundary

Decision: Verify reproducible brief output by comparing versioned exports from independent temporary databases after excluding only database-assigned identifiers and the processing timestamp.

Reasoning: Separate runs of the same normalized source should produce equivalent stable document metadata, provenance versions and fingerprint, brief findings, and evidence ordering. Deliberately varying generated identifiers ensures that the test does not pass accidentally because both databases begin with identical row numbers.

Trade-off: Raw exports from separate runs are not required to be byte-identical because `document.id`, `processing_run.id`, `processing_run.processed_at`, and `brief_id` identify a particular stored execution. The normalization helper remains test-only; no production comparison API or deterministic output fingerprint is introduced without a concrete integrity or interchange requirement.

## 2026-08-10 — Append-only reviewer decisions

Decision: Store reviewer decisions as separate append-only events linked to generated review focus areas or missing-information items in one persisted brief. Expose the controls only for persisted bundled briefs; an item without an event is displayed as `Unreviewed` without creating a database record.

Reasoning: Human review should be visible and revisable without mutating the generated brief or weakening extraction reproducibility. Stable brief, target-type, and target-index identities allow the Streamlit interface to reload the current effective state while preserving the earlier event history.

Trade-off: The current workflow has no reviewer identity, authentication, simultaneous multi-user editing, bulk actions, or decisions for session-only pasted excerpts. Generated review questions are not separate decision targets. The `1.0.0` export remains focused on the generated brief and processing provenance; including decision history requires a separate export-contract compatibility decision.

## 2026-08-12 — Export reviewer-decision history in schema 1.1.0

Decision: Retain schema `1.0.0` for explicit compatibility serialisation of the generated brief and processing provenance. Add current schema `1.1.0` to export the complete ordered append-only history of reviewer decisions for generated focus areas and information gaps.

Reasoning: Reviewer decisions are human-authored review data, separate from deterministic extraction and immutable generated briefs. Including their history makes the downloadable record more useful while preserving source evidence, extraction output, and processing provenance.

Trade-off: Schema `1.1.0` records decision events in ascending event-ID order, including the generated target type and position, state, optional note, and UTC decision timestamp. Reviewer decisions remain limited to persisted bundled briefs and generated `risk_domain` and `missing_info` targets. Session-only pasted excerpts, reviewer identity, authentication, simultaneous multi-user editing, and decisions for generated review questions remain unsupported.
