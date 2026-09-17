from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

from core.http_client import SafeHttpClient
from core.models import Candidate, ScanRecord
from core.parser import parse_html
from filter.alive_filter import is_analyzable
from filter.korea_relevance import classify_korea
from filter.result_filter import content_exclusion_reason
from filter.url_filter import normalize_url, site_id
from fingerprint.engine import FingerprintEngine


class Pipeline:
    def __init__(self, settings: dict, signatures: dict, client: SafeHttpClient) -> None:
        self.settings, self.client = settings, client
        self.engine = FingerprintEngine(signatures)

    async def scan(self, item: Candidate | str) -> ScanRecord:
        candidate = item if isinstance(item, Candidate) else Candidate(item, "manual", collected_at=datetime.now(timezone.utc).isoformat())
        url = normalize_url(candidate.url)
        fetched = await self.client.fetch(url)
        checked_at = datetime.now(timezone.utc).isoformat()
        final = fetched.final_url or url; host = urlparse(final).hostname or ""
        headers = {k.lower(): v for k, v in fetched.headers.items()}
        record = ScanRecord(
            site_id=site_id(url), original_url=candidate.url, normalized_url=url, final_url=final,
            domain=host, http_status=fetched.status, content_type=fetched.content_type,
            content_length=fetched.content_length, http_date=headers.get("date", ""),
            http_last_modified=headers.get("last-modified", ""), http_etag=headers.get("etag", ""),
            source=candidate.source, source_query=candidate.source_query,
            source_seen_at=candidate.source_seen_at, collected_at=candidate.collected_at,
            checked_at=checked_at, response_time=round(fetched.response_time, 4),
            response_time_ms=round(fetched.response_time * 1000, 2),
            scan_timestamp=checked_at, error=fetched.error,
        )
        if not is_analyzable(fetched): return record
        page = parse_html(fetched.body, final)
        record.exclusion_reason = content_exclusion_reason(page, final)
        kr = classify_korea(page, final, self.settings)
        detections = self.engine.detect_all(final, fetched.body, fetched.headers, {}, page)
        lovable = detections.get("lovable")
        claude = detections.get("claude")
        detection = self.engine.detect(final, fetched.body, fetched.headers, {}, page)
        record.page_title, record.html_lang = page.title, page.html_lang
        record.published_date = page.published_date
        record.korea_score, record.korea_class, record.hangul_ratio = kr.score, kr.classification, round(kr.hangul_ratio, 4)
        record.korea_evidence = kr.evidence
        if lovable:
            record.lovable_class = "LOVABLE_CONFIRMED" if lovable.score >= 80 else "LOVABLE_PROBABLE" if lovable.score >= 30 else "NO_LOVABLE_EVIDENCE"
            record.lovable_evidence = [{"signature": e.signature, "location": e.location, "value": e.value, "weight": e.weight} for e in lovable.evidence]
        if claude:
            record.claude_class = "CLAUDE_POSSIBLE" if claude.evidence else "NO_CLAUDE_EVIDENCE"
            record.claude_evidence = [{"signature": e.signature, "location": e.location, "value": e.value, "weight": e.weight} for e in claude.evidence]
        if record.lovable_class != "NO_LOVABLE_EVIDENCE" and record.claude_class == "CLAUDE_POSSIBLE": record.vibe_result = "LOVABLE_AND_CLAUDE_STYLE"
        elif record.lovable_class != "NO_LOVABLE_EVIDENCE": record.vibe_result = "LOVABLE"
        elif record.claude_class == "CLAUDE_POSSIBLE": record.vibe_result = "CLAUDE_POSSIBLE"
        record.builder, record.builder_score, record.builder_class = detection.builder, detection.score, detection.classification
        record.builder_evidence = [{"signature": e.signature, "location": e.location, "value": e.value, "weight": e.weight} for e in detection.evidence]
        record.framework, record.external_domains = detection.framework, page.external_domains
        record.libraries = sorted({str(value) for key, value in detection.framework.items() if key != "framework"})
        record.needs_deep_scan = bool((lovable and lovable.needs_deep_scan) or (claude and claude.needs_deep_scan))
        return record

    async def scan_many(self, urls: list[Candidate | str], callback=None) -> list[ScanRecord]:
        async def run(index: int, url: Candidate | str):
            result = await self.scan(url)
            if callback: callback(index, len(urls), result)
            return result
        return await asyncio.gather(*(run(i + 1, u) for i, u in enumerate(urls)))
