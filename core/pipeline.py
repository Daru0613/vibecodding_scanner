from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from urllib.parse import urlparse

from core import dns_client
from core.http_client import SafeHttpClient
from core.models import ScanRecord
from core.parser import parse_html
from filter.alive_filter import is_analyzable
from filter.korea_relevance import classify_korea
from filter.url_filter import site_id
from fingerprint.engine import FingerprintEngine


class Pipeline:
    def __init__(self, settings: dict, signatures: dict, client: SafeHttpClient) -> None:
        self.settings, self.client = settings, client
        self.engine = FingerprintEngine(signatures)

    async def scan(self, url: str) -> ScanRecord:
        fetched = await self.client.fetch(url)
        final = fetched.final_url or url; host = urlparse(final).hostname or ""
        record = ScanRecord(site_id(url), url, final, host, fetched.status, response_time=round(fetched.response_time, 4), scan_timestamp=datetime.now(timezone.utc).isoformat(), error=fetched.error)
        if not is_analyzable(fetched): return record
        page = parse_html(fetched.body, final)
        kr = classify_korea(page, final, self.settings)
        dns = await dns_client.lookup(host)
        detection = self.engine.detect(final, fetched.body, fetched.headers, dns, page)
        # Only ambiguous builder candidates get a bounded second pass. No link crawling.
        if detection.needs_deep_scan:
            scripts: dict[str, str] = {}
            maximum = int(self.settings.get("http", {}).get("max_js_files", 3))
            for script_url in page.scripts[:maximum]:
                script_result = await self.client.fetch(script_url)
                if script_result.status == 200 and script_result.body:
                    scripts[script_url] = script_result.body
            if scripts:
                detection = self.engine.detect(final, fetched.body, fetched.headers, dns, page, scripts)
        record.page_title, record.html_lang = page.title, page.html_lang
        record.published_date = page.published_date
        record.korea_score, record.korea_class, record.hangul_ratio = kr.score, kr.classification, round(kr.hangul_ratio, 4)
        record.builder, record.builder_score, record.builder_class = detection.builder, detection.score, detection.classification
        record.builder_evidence = [{"signature": e.signature, "location": e.location, "value": e.value, "weight": e.weight} for e in detection.evidence]
        record.framework, record.external_domains, record.needs_deep_scan = detection.framework, page.external_domains, detection.needs_deep_scan
        return record

    async def scan_many(self, urls: list[str], callback=None) -> list[ScanRecord]:
        async def run(index: int, url: str):
            result = await self.scan(url)
            if callback: callback(index, len(urls), result)
            return result
        return await asyncio.gather(*(run(i + 1, u) for i, u in enumerate(urls)))
