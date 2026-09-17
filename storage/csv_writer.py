from __future__ import annotations

import csv
import json
from pathlib import Path

from core.models import ScanRecord


class CsvWriter:
    def __init__(self, path: str) -> None:
        self.path = Path(path); self.file = None; self.writer = None
    def write(self, record: ScanRecord) -> None:
        row = record.csv_dict()
        for key in ("builder_evidence", "framework", "external_domains"): row[key] = json.dumps(row[key], ensure_ascii=False)
        if self.file is None:
            new = not self.path.exists() or self.path.stat().st_size == 0
            self.file = self.path.open("a", newline="", encoding="utf-8-sig")
            self.writer = csv.DictWriter(self.file, fieldnames=list(row));
            if new: self.writer.writeheader()
        self.writer.writerow(row); self.file.flush()
    def close(self) -> None:
        if self.file: self.file.close()
