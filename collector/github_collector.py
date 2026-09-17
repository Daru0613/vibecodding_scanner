from __future__ import annotations

import os
import re
import httpx

from collector.base import Collector

URL = re.compile(r"https?://[^\s<>'\"\)\]]+")


class GitHubCollector(Collector):
    """Finds explicitly published project/homepage URLs in public GitHub metadata."""

    def __init__(self, queries: list[str]) -> None: self.queries = queries

    async def collect(self, limit: int) -> list[str]:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "OpenWeb-KR-Research/1.0"}
        if token := os.getenv("GITHUB_TOKEN"): headers["Authorization"] = f"Bearer {token}"
        found: list[str] = []
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            for query in self.queries:
                try:
                    response = await client.get("https://api.github.com/search/repositories", params={"q": query, "sort": "updated", "per_page": min(30, limit)})
                    response.raise_for_status()
                    for repo in response.json().get("items", []):
                        homepage = (repo.get("homepage") or "").strip()
                        if homepage.startswith(("http://", "https://")): found.append(homepage)
                        description = repo.get("description") or ""
                        found.extend(URL.findall(description))
                        if len(found) >= limit: return found[:limit]
                except Exception: continue
        return found[:limit]
