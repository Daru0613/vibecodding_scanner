from __future__ import annotations

import os
import httpx

from collector.base import Collector, candidate
from core.models import Candidate


class SearchCollector(Collector):
    """Search API collector. Credentials are read only from environment variables."""

    def __init__(self, queries: list[str], provider: str = "brave") -> None:
        self.queries, self.provider = queries, provider

    async def collect(self, limit: int) -> list[Candidate]:
        if self.provider == "brave":
            return await self._brave(limit)
        if self.provider == "google":
            return await self._google(limit)
        return []

    async def _brave(self, limit: int) -> list[Candidate]:
        key = os.getenv("BRAVE_SEARCH_API_KEY")
        if not key: return []
        found: list[Candidate] = []
        async with httpx.AsyncClient(timeout=20, headers={"X-Subscription-Token": key, "User-Agent": "OpenWeb-KR-Research/1.0"}) as client:
            for query in self.queries:
                try:
                    response = await client.get("https://api.search.brave.com/res/v1/web/search", params={"q": query, "count": min(20, limit)})
                    response.raise_for_status()
                    found.extend(candidate(item["url"], "search_brave", query) for item in response.json().get("web", {}).get("results", []) if item.get("url"))
                except Exception: continue
                if len(found) >= limit: break
        return found[:limit]

    async def _google(self, limit: int) -> list[Candidate]:
        key, engine = os.getenv("GOOGLE_API_KEY"), os.getenv("GOOGLE_CSE_ID")
        if not key or not engine: return []
        found: list[Candidate] = []
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": "OpenWeb-KR-Research/1.0"}) as client:
            for query in self.queries:
                try:
                    response = await client.get("https://www.googleapis.com/customsearch/v1", params={"key": key, "cx": engine, "q": query, "num": min(10, limit)})
                    response.raise_for_status()
                    found.extend(candidate(item["link"], "search_google", query) for item in response.json().get("items", []) if item.get("link"))
                except Exception: continue
                if len(found) >= limit: break
        return found[:limit]
