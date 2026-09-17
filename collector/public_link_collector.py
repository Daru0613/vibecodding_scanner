from __future__ import annotations

import re
from pathlib import Path

from collector.base import Collector, candidate
from core.models import Candidate

URL = re.compile(r"https?://[^\s<>'\"]+")


class PublicLinkCollector(Collector):
    def __init__(self, paths: list[str]) -> None: self.paths = paths
    async def collect(self, limit: int) -> list[Candidate]:
        out: list[Candidate] = []
        for name in self.paths:
            path = Path(name)
            if path.is_file(): out.extend(candidate(url, "public_file", name) for url in URL.findall(path.read_text(encoding="utf-8", errors="ignore")))
            if len(out) >= limit: break
        return out[:limit]

