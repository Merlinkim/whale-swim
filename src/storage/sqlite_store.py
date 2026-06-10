from __future__ import annotations

from collections.abc import Iterable
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from src.models.paper import Paper, merge_tokens


SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
authors TEXT,
published_date TEXT,
year INTEGER,
source TEXT,
topic TEXT,
keyword TEXT,
url TEXT,
doi TEXT,
arxiv_id TEXT,
unique_key TEXT UNIQUE,
first_seen_at TEXT,
last_seen_at TEXT
);
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authors_to_text(authors: list[str]) -> str:
    return json.dumps(authors, ensure_ascii=False)


def _authors_from_text(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in value.split(";") if item.strip()]


def _merge_text(existing: str | None, incoming: str | None) -> str | None:
    values: list[str] = []
    for item in (existing, incoming):
        if not item:
            continue
        for token in item.split(","):
            cleaned = token.strip()
            if cleaned and cleaned not in values:
                values.append(cleaned)
    return ", ".join(values) if values else None


class SQLitePaperStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        self.connection.execute(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def upsert_many(self, papers: Iterable[Paper]) -> int:
        affected = 0
        for paper in papers:
            self.upsert(paper)
            affected += 1
        return affected

    def upsert(self, paper: Paper) -> None:
        now = _utc_now()
        unique_key = paper.unique_key()
        existing = self.connection.execute(
            "SELECT * FROM papers WHERE unique_key = ?",
            (unique_key,),
        ).fetchone()

        if existing is None:
            self.connection.execute(
                """
                INSERT INTO papers (
                    title, authors, published_date, year, source, topic, keyword,
                    url, doi, arxiv_id, unique_key, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper.title,
                    _authors_to_text(paper.authors),
                    paper.published_date,
                    paper.year,
                    paper.source,
                    paper.topic,
                    paper.keyword,
                    paper.url,
                    paper.doi,
                    paper.arxiv_id,
                    unique_key,
                    now,
                    now,
                ),
            )
            self.connection.commit()
            return

        merged = {
            "title": existing["title"] or paper.title,
            "authors": _merge_authors(existing["authors"], paper.authors),
            "published_date": existing["published_date"] or paper.published_date,
            "year": existing["year"] or paper.year,
            "source": _merge_text(existing["source"], paper.source) or existing["source"] or paper.source,
            "topic": _merge_text(existing["topic"], paper.topic) or existing["topic"] or paper.topic,
            "keyword": _merge_text(existing["keyword"], paper.keyword) or existing["keyword"] or paper.keyword,
            "url": existing["url"] or paper.url,
            "doi": existing["doi"] or paper.doi,
            "arxiv_id": existing["arxiv_id"] or paper.arxiv_id,
        }

        self.connection.execute(
            """
            UPDATE papers
            SET title = ?, authors = ?, published_date = ?, year = ?, source = ?,
                topic = ?, keyword = ?, url = ?, doi = ?, arxiv_id = ?,
                last_seen_at = ?
            WHERE unique_key = ?
            """,
            (
                merged["title"],
                _authors_to_text(merged["authors"]),
                merged["published_date"],
                merged["year"],
                merged["source"],
                merged["topic"],
                merged["keyword"],
                merged["url"],
                merged["doi"],
                merged["arxiv_id"],
                now,
                unique_key,
            ),
        )
        self.connection.commit()

    def list_papers(self) -> list[dict[str, object]]:
        rows = self.connection.execute("SELECT * FROM papers").fetchall()
        papers: list[dict[str, object]] = []
        for row in rows:
            papers.append(
                {
                    "title": row["title"],
                    "authors": _authors_from_text(row["authors"]),
                    "published_date": row["published_date"],
                    "year": row["year"],
                    "source": row["source"],
                    "topic": row["topic"],
                    "keyword": row["keyword"],
                    "url": row["url"],
                    "doi": row["doi"],
                    "arxiv_id": row["arxiv_id"],
                    "unique_key": row["unique_key"],
                    "first_seen_at": row["first_seen_at"],
                    "last_seen_at": row["last_seen_at"],
                }
            )
        return papers

    def count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM papers").fetchone()[0])


def _merge_authors(existing_text: str | None, incoming_authors: list[str]) -> list[str]:
    authors = _authors_from_text(existing_text)
    merged: list[str] = []
    for author in authors + incoming_authors:
        if author and author not in merged:
            merged.append(author)
    return merged
