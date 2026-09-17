from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from core.models import Candidate, ScanRecord
from filter.url_filter import classify_url, is_public_http_url, normalize_url, site_id


class CollectorState:
    """Durable candidate queue and completed-scan ledger."""

    def __init__(self, path: str = "collector.db") -> None:
        self.conn = sqlite3.connect(Path(path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                url TEXT PRIMARY KEY,
                normalized_url TEXT NOT NULL UNIQUE,
                site_key TEXT UNIQUE,
                source TEXT,
                source_query TEXT,
                source_seen_at TEXT,
                collected_at TEXT,
                url_type TEXT,
                status TEXT NOT NULL DEFAULT 'pending'
            );
            CREATE TABLE IF NOT EXISTS scanned (
                normalized_url TEXT PRIMARY KEY,
                site_key TEXT UNIQUE,
                final_url TEXT,
                http_status INTEGER,
                checked_at TEXT,
                result_written INTEGER NOT NULL DEFAULT 0,
                payload TEXT
            );
            """
        )
        self._ensure_column("candidates", "url_type", "TEXT")
        self._ensure_column("candidates", "site_key", "TEXT")
        self._ensure_column("scanned", "site_key", "TEXT")
        self._ensure_column("scanned", "payload", "TEXT")
        self.conn.commit()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = {row[1] for row in self.conn.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def add_candidates(self, candidates: list[Candidate]) -> tuple[int, int]:
        added = excluded = 0
        for item in candidates:
            normalized = normalize_url(item.url)
            item.url_type = classify_url(normalized)
            if not normalized or not is_public_http_url(normalized) or item.url_type in {"REPOSITORY", "SOURCE_FILE", "DOCUMENT", "NON_HTML"}:
                excluded += 1
                continue
            normalized = normalized.replace("http://", "https://", 1)
            before = self.conn.total_changes
            self.conn.execute(
                "INSERT OR IGNORE INTO candidates "
                "(url,normalized_url,site_key,source,source_query,source_seen_at,collected_at,url_type,status) "
                "VALUES (?,?,?,?,?,?,?,?,'pending')",
                (item.url, normalized, site_id(normalized), item.source, item.source_query, item.source_seen_at,
                 item.collected_at, item.url_type),
            )
            added += self.conn.total_changes > before
        self.conn.commit()
        return added, excluded

    def reset(self) -> None:
        self.conn.execute("DELETE FROM candidates")
        self.conn.execute("DELETE FROM scanned")
        self.conn.commit()

    def has_scanned_final(self, final_url: str) -> bool:
        return self.conn.execute("SELECT 1 FROM scanned WHERE site_key=?", (site_id(final_url),)).fetchone() is not None

    def pending(self, limit: int = 100) -> list[Candidate]:
        rows = self.conn.execute(
            "SELECT url,source,source_query,source_seen_at,collected_at,url_type "
            "FROM candidates WHERE status='pending' ORDER BY rowid LIMIT ?", (limit,)
        ).fetchall()
        return [Candidate(*row) for row in rows]

    def complete(self, candidate: Candidate, record: ScanRecord, result_written: bool) -> None:
        normalized = (normalize_url(record.final_url) or record.normalized_url or normalize_url(candidate.url)).replace("http://", "https://", 1)
        self.conn.execute(
            "INSERT OR IGNORE INTO scanned "
            "(normalized_url,site_key,final_url,http_status,checked_at,result_written,payload) VALUES (?,?,?,?,?,?,?)",
            (normalized, site_id(record.final_url or normalized), record.final_url, record.http_status,
             record.checked_at, int(result_written), json.dumps(asdict(record), ensure_ascii=False)),
        )
        candidate_key = normalize_url(candidate.url).replace("http://", "https://", 1)
        self.conn.execute("UPDATE candidates SET status='completed' WHERE normalized_url=?", (candidate_key,))
        self.conn.commit()

    def counts(self) -> dict[str, int]:
        total = self.conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        completed = self.conn.execute("SELECT COUNT(*) FROM candidates WHERE status='completed'").fetchone()[0]
        return {"total": total, "completed": completed, "pending": total - completed}

    def close(self) -> None:
        self.conn.close()
