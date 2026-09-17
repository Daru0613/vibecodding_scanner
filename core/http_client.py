from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx

from core.cache import ResponseCache
from core.models import FetchResult
from core.rate_limiter import RateLimiter
from filter.url_filter import is_public_http_url


class UnsafeDestination(Exception):
    pass


class SafeHttpClient:
    def __init__(self, settings: dict, cache: ResponseCache | None = None) -> None:
        http = settings.get("http", {})
        self.max_size = int(http.get("max_response_size", 2_097_152))
        self.retries = int(http.get("retry", 1))
        self.cache = cache
        self.limiter = RateLimiter(int(http.get("global_concurrency", 10)), int(http.get("per_domain_concurrency", 1)))
        timeout = httpx.Timeout(float(http.get("read_timeout", 10)), connect=float(http.get("connect_timeout", 5)))
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True,
                                        max_redirects=int(http.get("max_redirects", 5)),
                                        headers={"User-Agent": http.get("user_agent", "OpenWeb-KR-Research/1.0")},
                                        event_hooks={"request": [self._validate_destination]})
        self.requests = self.cache_hits = 0
        self.status_counts: dict[str, int] = {}

    async def fetch(self, url: str) -> FetchResult:
        if not is_public_http_url(url):
            return FetchResult(url, error="non-public or invalid destination blocked")
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
                    if status == 429:
                        retry_after = response.headers.get("retry-after", "")
                        return FetchResult(url, str(response.url), status, dict(response.headers), response_time=time.perf_counter()-started, redirect_count=len(response.history), error=f"rate limited; retry-after={retry_after}")
                    if status == 503:
                        return FetchResult(url, str(response.url), status, dict(response.headers), response_time=time.perf_counter()-started, redirect_count=len(response.history), error="service unavailable")
                    content_type = response.headers.get("content-type", "")
                    try:
                        declared = int(response.headers.get("content-length", "0") or 0)
                    except ValueError:
                        declared = 0
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
                    lowered = body[:200_000].lower()
                    blocked = any(marker in lowered for marker in ("captcha", "access denied", "cf-chl-", "waf challenge"))
                    error = "CAPTCHA/WAF/access denied" if blocked else ""
                    return FetchResult(url, str(response.url), status, dict(response.headers), body, content_type, len(data), time.perf_counter()-started, len(response.history), error)
            except UnsafeDestination:
                return FetchResult(url, error="non-public redirect destination blocked", response_time=time.perf_counter()-started)
            except (httpx.TimeoutException, httpx.NetworkError, httpx.TooManyRedirects) as exc:
                if attempt < self.retries: continue
                return FetchResult(url, error=type(exc).__name__, response_time=time.perf_counter()-started)
        return FetchResult(url, error="request failed")

    async def close(self) -> None: await self.client.aclose()

    async def _validate_destination(self, request: httpx.Request) -> None:
        url = str(request.url)
        if not is_public_http_url(url):
            raise UnsafeDestination(url)
        host = request.url.host
        try:
            rows = await asyncio.get_running_loop().getaddrinfo(host, request.url.port or 443, type=socket.SOCK_STREAM)
        except OSError:
            return
        for row in rows:
            address = ipaddress.ip_address(row[4][0])
            if (address.is_private or address.is_loopback or address.is_link_local or
                    address.is_reserved or address.is_multicast or address.is_unspecified):
                raise UnsafeDestination(url)


def _retry_after(value: str | None) -> float:
    if not value: return 1.0
    try: return max(0.0, float(value))
    except ValueError:
        try: return max(0.0, (parsedate_to_datetime(value).timestamp() - time.time()))
        except Exception: return 1.0
