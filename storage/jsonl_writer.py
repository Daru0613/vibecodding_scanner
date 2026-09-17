from __future__ import annotations

import json
from pathlib import Path
from core.models import ScanRecord


class JsonlWriter:
    def __init__(self, path: str) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        self.file = output.open("a", encoding="utf-8")
    def write(self, record: ScanRecord) -> None:
        data = record.to_dict()
        data["korea"] = {"class": record.korea_class, "score": record.korea_score,
                          "hangul_ratio": record.hangul_ratio, "evidence": record.korea_evidence}
        data["lovable"] = {"class": record.lovable_class, "evidence": record.lovable_evidence}
        data["claude"] = {"class": record.claude_class, "evidence": record.claude_evidence}
        self.file.write(json.dumps(data, ensure_ascii=False) + "\n"); self.file.flush()
    def close(self) -> None: self.file.close()

