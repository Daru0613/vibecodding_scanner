from __future__ import annotations

import json
from pathlib import Path
from core.models import ScanRecord


class JsonlWriter:
    def __init__(self, path: str) -> None: self.file = Path(path).open("a", encoding="utf-8")
    def write(self, record: ScanRecord) -> None:
        self.file.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n"); self.file.flush()
    def close(self) -> None: self.file.close()

