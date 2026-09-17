from __future__ import annotations

import os
import re
import httpx

from collector.base import Collector, candidate
from core.models import Candidate

URL = re.compile(r"https?://[^\s<>'\"\)\]]+")
DEPLOYMENT_WORD = re.compile(r"\b(?:live|demo|website|preview|deployment|deployed|homepage)\b", re.I)
DEPLOYMENT_HOST = re.compile(r"(?:lovable\.app|vercel\.app|netlify\.app|pages\.dev|replit\.app|base44\.app|railway\.app|onrender\.com)", re.I)


def deployment_urls(text: str) -> list[str]:
    found: list[str] = []
    for line in text.splitlines():
        urls = URL.findall(line)
        if DEPLOYMENT_WORD.search(line) or any(DEPLOYMENT_HOST.search(url) for url in urls):
            found.extend(urls)
    return found


class GitHubCollector(Collector):
    """Finds explicitly published project/homepage URLs in public GitHub metadata."""

    def __init__(self, queries: list[str]) -> None: self.queries = queries

    async def collect(self, limit: int) -> list[Candidate]:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "OpenWeb-KR-Research/1.0"}
        if token := os.getenv("GITHUB_TOKEN"): headers["Authorization"] = f"Bearer {token}"
        found: list[Candidate] = []
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            for query in self.queries:
                try:
                    response = await client.get("https://api.github.com/search/repositories", params={"q": query, "sort": "updated", "per_page": min(30, limit)})
                    response.raise_for_status()
                    for repo in response.json().get("items", []):
                        homepage = (repo.get("homepage") or "").strip()
                        if homepage.startswith(("http://", "https://")): found.append(candidate(homepage, "github_metadata", query))
                        description = repo.get("description") or ""
                        found.extend(candidate(url, "github_description", query) for url in deployment_urls(description))
                        readme_url = repo.get("url", "") + "/readme"
                        if readme_url:
                            try:
                                readme = await client.get(readme_url, headers={**headers, "Accept": "application/vnd.github.raw+json"})
                                if readme.status_code == 200:
                                    found.extend(candidate(url, "github_readme", query) for url in deployment_urls(readme.text))
                            except httpx.HTTPError:
                                pass
                        if len(found) >= limit: return found[:limit]
                except Exception: continue
        return found[:limit]
