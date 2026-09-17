from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from core.models import FetchResult


class ResponseCache:
    def __init__(self, path: str = "cache.sqlite") -> None:
        self.conn = sqlite3.connect(Path(path))
        self.conn.execute("CREATE TABLE IF NOT EXISTS responses (url TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        self.conn.commit()

    def get(self, url: str) -> FetchResult | None:
        row = self.conn.execute("SELECT payload FROM responses WHERE url=?", (url,)).fetchone()
        if not row:
            return None
        data = json.loads(row[0]); data["from_cache"] = True
        return FetchResult(**data)

    def put(self, result: FetchResult) -> None:
        data = asdict(result); data["from_cache"] = False
        self.conn.execute("INSERT OR REPLACE INTO responses VALUES (?,?)", (result.original_url, json.dumps(data, ensure_ascii=False)))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

