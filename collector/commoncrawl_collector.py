from __future__ import annotations

import json
import httpx
from datetime import datetime, timezone
from urllib.parse import urlsplit

from collector.base import Collector, candidate
from core.models import Candidate


class CommonCrawlCollector(Collector):
    def __init__(self, index: str = "latest", queries: list[str] | None = None) -> None:
        self.index, self.queries = index, queries or ["*.lovable.app/*"]
    async def collect(self, limit: int) -> list[Candidate]:
        out: list[Candidate] = []
        seen_hosts: set[str] = set()
        async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "OpenWeb-KR-Research/1.0"}) as client:
            index = self.index
            if index == "latest":
                try:
                    indexes = (await client.get("https://index.commoncrawl.org/collinfo.json")).json()
                    index = indexes[0]["id"]
                except Exception:
                    return out
            for query in self.queries:
                try:
                    r = await client.get(f"https://index.commoncrawl.org/{index}-index", params={"url": query, "output": "json", "filter": "status:200", "collapse": "urlkey"})
                    for line in r.text.splitlines():
                        try:
                            row = json.loads(line)
                            host = (urlsplit(row["url"]).hostname or "").lower()
                            if not host or host in seen_hosts:
                                continue
                            seen_hosts.add(host)
                            stamp = row.get("timestamp", "")
                            if len(stamp) == 14 and stamp.isdigit():
                                stamp = datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).isoformat()
                            out.append(candidate(row["url"], "commoncrawl", query, stamp))
                        except Exception: pass
                        if len(out) >= limit: return out
                except Exception: continue
        return out
