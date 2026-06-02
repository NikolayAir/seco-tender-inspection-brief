"""SQLite storage layer.

Two tables: `documents` (one structured record per tender) and `briefs` (one
inspection brief per document). List fields and evidence are stored as JSON text
to keep the first skeleton simple; a normalized evidence table is a later step.

All functions take an explicit ``db_path`` so tests can use a temporary database
and never touch the real ``data/processed/seco.db``.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.models import EvidenceSnippet, InspectionBrief, TenderDocument

DEFAULT_DB_PATH = Path("data") / "processed" / "seco.db"


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection, creating the parent folder if needed."""
    path = Path(db_path)
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create the tables if they do not exist (idempotent)."""
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source      TEXT NOT NULL,
                source_url  TEXT,
                title       TEXT NOT NULL,
                raw_text    TEXT NOT NULL,
                clean_text  TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS briefs (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id           INTEGER NOT NULL REFERENCES documents(id),
                summary               TEXT NOT NULL,
                technical_scopes      TEXT NOT NULL DEFAULT '[]',
                risk_domains          TEXT NOT NULL DEFAULT '[]',
                missing_info          TEXT NOT NULL DEFAULT '[]',
                review_questions      TEXT NOT NULL DEFAULT '[]',
                evidence              TEXT NOT NULL DEFAULT '[]',
                confidence            TEXT NOT NULL DEFAULT 'low',
                human_review_required INTEGER NOT NULL DEFAULT 1,
                created_at            TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )


def insert_document(document: TenderDocument, db_path: Path | str = DEFAULT_DB_PATH) -> int:
    """Insert a document and return its new id."""
    with connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO documents (source, source_url, title, raw_text, clean_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                document.source,
                document.source_url,
                document.title,
                document.raw_text,
                document.clean_text,
            ),
        )
        return int(cur.lastrowid)


def find_document_id(
    source: str, title: str, db_path: Path | str = DEFAULT_DB_PATH
) -> int | None:
    """Return the id of an existing document with this (source, title), or None."""
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM documents WHERE source = ? AND title = ? ORDER BY id LIMIT 1",
            (source, title),
        ).fetchone()
    return int(row["id"]) if row is not None else None


def update_document(
    document_id: int, document: TenderDocument, db_path: Path | str = DEFAULT_DB_PATH
) -> None:
    """Refresh an existing document's content so re-runs reflect sample edits."""
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE documents
            SET source_url = ?, raw_text = ?, clean_text = ?
            WHERE id = ?
            """,
            (document.source_url, document.raw_text, document.clean_text, document_id),
        )


def delete_briefs_for_document(
    document_id: int, db_path: Path | str = DEFAULT_DB_PATH
) -> None:
    """Remove any briefs linked to a document (used to replace on re-run)."""
    with connect(db_path) as conn:
        conn.execute("DELETE FROM briefs WHERE document_id = ?", (document_id,))


def insert_brief(
    document_id: int, brief: InspectionBrief, db_path: Path | str = DEFAULT_DB_PATH
) -> int:
    """Insert a brief linked to a document and return its new id."""
    with connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO briefs (
                document_id, summary, technical_scopes, risk_domains,
                missing_info, review_questions, evidence, confidence,
                human_review_required
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                brief.summary,
                json.dumps(brief.technical_scopes),
                json.dumps(brief.risk_domains),
                json.dumps(brief.missing_info),
                json.dumps(brief.review_questions),
                json.dumps([e.model_dump() for e in brief.evidence]),
                brief.confidence,
                int(brief.human_review_required),
            ),
        )
        return int(cur.lastrowid)


def get_documents(db_path: Path | str = DEFAULT_DB_PATH) -> list[dict]:
    """Return all documents as dicts, newest first."""
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def get_brief_for_document(
    document_id: int, db_path: Path | str = DEFAULT_DB_PATH
) -> InspectionBrief | None:
    """Return the most recent brief for a document, or None if absent."""
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM briefs WHERE document_id = ? ORDER BY id DESC LIMIT 1",
            (document_id,),
        ).fetchone()
    if row is None:
        return None
    return InspectionBrief(
        summary=row["summary"],
        technical_scopes=json.loads(row["technical_scopes"]),
        risk_domains=json.loads(row["risk_domains"]),
        missing_info=json.loads(row["missing_info"]),
        review_questions=json.loads(row["review_questions"]),
        evidence=[EvidenceSnippet(**e) for e in json.loads(row["evidence"])],
        confidence=row["confidence"],
        human_review_required=bool(row["human_review_required"]),
    )
