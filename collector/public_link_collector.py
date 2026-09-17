from __future__ import annotations

import re
from pathlib import Path

from collector.base import Collector

URL = re.compile(r"https?://[^\s<>'\"]+")


class PublicLinkCollector(Collector):
    def __init__(self, paths: list[str]) -> None: self.paths = paths
    async def collect(self, limit: int) -> list[str]:
        out: list[str] = []
        for name in self.paths:
            path = Path(name)
            if path.is_file(): out.extend(URL.findall(path.read_text(encoding="utf-8", errors="ignore")))
            if len(out) >= limit: break
        return out[:limit]

