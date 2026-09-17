from __future__ import annotations

import json
import httpx

from collector.base import Collector


class CommonCrawlCollector(Collector):
    def __init__(self, index: str = "latest", queries: list[str] | None = None) -> None:
        self.index, self.queries = index, queries or ["*.lovable.app/*"]
    async def collect(self, limit: int) -> list[str]:
        out: list[str] = []
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
                        try: out.append(json.loads(line)["url"])
                        except Exception: pass
                        if len(out) >= limit: return out
                except Exception: continue
        return out
