from __future__ import annotations

import asyncio
import time
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx

from core.cache import ResponseCache
from core.models import FetchResult
from core.rate_limiter import RateLimiter


class SafeHttpClient:
    def __init__(self, settings: dict, cache: ResponseCache | None = None) -> None:
        http = settings.get("http", {})
        self.max_size = int(http.get("max_response_size", 2_097_152))
        self.retries = int(http.get("retry", 1))
        self.cache = cache
        self.limiter = RateLimiter(int(http.get("global_concurrency", 10)), int(http.get("per_domain_concurrency", 1)))
        timeout = httpx.Timeout(float(http.get("read_timeout", 10)), connect=float(http.get("connect_timeout", 5)))
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=int(http.get("max_redirects", 5)), headers={"User-Agent": http.get("user_agent", "OpenWeb-KR-Research/1.0")})
        self.requests = self.cache_hits = 0
        self.status_counts: dict[str, int] = {}

    async def fetch(self, url: str) -> FetchResult:
        if self.cache and (hit := self.cache.get(url)):
            self.cache_hits += 1; return hit
        host = urlparse(url).hostname or ""
        async with self.limiter.limit(host):
            result = await self._request(url)
        if self.cache and (result.status or result.error): self.cache.put(result)
        return result

    async def _request(self, url: str) -> FetchResult:
        for attempt in range(self.retries + 1):
            started = time.perf_counter(); self.requests += 1
            try:
                async with self.client.stream("GET", url) as response:
                    status = response.status_code
                    self.status_counts[str(status)] = self.status_counts.get(str(status), 0) + 1
                    if status in (401, 403):
                        return FetchResult(url, str(response.url), status, dict(response.headers), response_time=time.perf_counter()-started, redirect_count=len(response.history), error="access blocked")
                    if status == 429 and attempt < self.retries:
                        wait = min(_retry_after(response.headers.get("retry-after")), 10); await asyncio.sleep(wait); continue
                    if status == 503 and attempt < self.retries:
                        await asyncio.sleep(1 + attempt); continue
                    content_type = response.headers.get("content-type", "")
                    declared = int(response.headers.get("content-length", "0") or 0)
                    if declared > self.max_size:
                        return FetchResult(url, str(response.url), status, dict(response.headers), content_type=content_type, content_length=declared, response_time=time.perf_counter()-started, redirect_count=len(response.history), error="response too large")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > self.max_size: break
                    if len(data) > self.max_size:
                        return FetchResult(url, str(response.url), status, dict(response.headers), content_type=content_type, content_length=len(data), response_time=time.perf_counter()-started, redirect_count=len(response.history), error="response too large")
                    textual = any(kind in content_type.lower() for kind in ("html", "javascript", "text/", "json"))
                    body = bytes(data).decode(response.encoding or "utf-8", errors="replace") if textual else ""
                    return FetchResult(url, str(response.url), status, dict(response.headers), body, content_type, len(data), time.perf_counter()-started, len(response.history))
            except (httpx.TimeoutException, httpx.NetworkError, httpx.TooManyRedirects) as exc:
                if attempt < self.retries: continue
                return FetchResult(url, error=type(exc).__name__, response_time=time.perf_counter()-started)
        return FetchResult(url, error="request failed")

    async def close(self) -> None: await self.client.aclose()


def _retry_after(value: str | None) -> float:
    if not value: return 1.0
    try: return max(0.0, float(value))
    except ValueError:
        try: return max(0.0, (parsedate_to_datetime(value).timestamp() - time.time()))
        except Exception: return 1.0
