from __future__ import annotations

import httpx

from collector.base import Collector, candidate
from core.models import Candidate


class CTCollector(Collector):
    """Queries crt.sh's public certificate index; no subdomain brute forcing."""
    def __init__(self, queries: list[str] | None = None) -> None: self.queries = queries or ["%.lovable.app"]
    async def collect(self, limit: int) -> list[Candidate]:
        found: list[Candidate] = []
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": "OpenWeb-KR-Research/1.0"}) as client:
            for query in self.queries:
                try:
                    response = await client.get("https://crt.sh/", params={"q": query, "output": "json"})
                    response.raise_for_status()
                    for row in response.json():
                        for host in row.get("name_value", "").splitlines():
                            if "*" not in host:
                                seen = row.get("entry_timestamp") or row.get("not_before") or ""
                                found.append(candidate("https://" + host.strip().lower(), "ct", query, seen))
                            if len(found) >= limit: return found
                except Exception: continue
        return found

