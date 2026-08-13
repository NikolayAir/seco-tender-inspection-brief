# Tender-to-Inspection Brief — Product Brief

## Product purpose

Tender-to-Inspection Brief helps technical reviewers turn public construction tender excerpts into structured, source-traced review briefs.

The application supports early review preparation by identifying relevant technical scopes, surfacing information gaps, suggesting follow-up questions, and linking detected review domains to source evidence.

It supports human technical review and does not make legal, regulatory, compliance, safety, or engineering decisions.

## Primary users

* Technical reviewers
* Inspection coordinators
* Specialists preparing for an early tender, document, or design review

## User problem

Public construction tender documents can contain important technical signals across scope descriptions, referenced surveys, attachments, project constraints, and specialist interfaces.

Reviewers need a faster and more consistent way to:

* understand the declared project scope;
* identify technical domains requiring attention;
* locate supporting source evidence;
* highlight missing or unclear information;
* prepare focused follow-up questions;
* record and revisit decisions on persisted generated findings.

## Product value

The application provides a transparent first-pass review structure without hiding how findings were produced.

A useful result should help the reviewer understand the project, inspect detected domains and their evidence, identify information gaps, record decisions, and decide what requires further investigation.

## Inputs

The application currently accepts:

* bundled public construction tender excerpts with recorded source metadata;
* short public, non-confidential excerpts pasted into the Streamlit interface.

Results generated from bundled samples are persisted. Pasted excerpts are processed only in the current session and are not stored.

## Outputs

Each structured review brief contains:

* a short project summary;
* detected technical scopes and review domains;
* missing or unclear information;
* suggested reviewer questions;
* source-labelled evidence snippets;
* an explicit confidence level;
* a human-review-required flag.

Persisted bundled briefs can also be downloaded as deterministic, versioned JSON. Each export contains document metadata, the exact linked processing run, the complete generated brief and source evidence, and the complete ordered reviewer-decision history.

For persisted bundled briefs, reviewers can save `accepted`, `rejected`, or `needs_follow_up` decisions and optional notes for generated review focus areas and information gaps. Each saved change appends a new event, so earlier decisions remain available as history.

## Product boundary

The application focuses on early technical-review preparation. It does not currently provide:

* complete tender-dossier ingestion or document management;
* BIM coordination, site-inspection records, or defect tracking;
* regulatory or compliance assessment;
* autonomous engineering decisions;
* persistent storage of pasted excerpts;
* multi-user review workflows;
* reviewer identity or authentication;
* general multilingual or semantic document understanding.

## Product direction

Near-term priorities are:

* broader qualitative validation;
* documented ingestion of tender documents and PDFs;
* stronger extraction methods only when they can be evaluated against the transparent baseline.
