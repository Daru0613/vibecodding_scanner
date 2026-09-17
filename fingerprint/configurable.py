from __future__ import annotations

import fnmatch
import re
from urllib.parse import urlparse

from core.models import DetectionResult, Evidence, PageData
from core.scoring import score_class
from fingerprint.base import FingerprintDetector


class ConfigurableDetector(FingerprintDetector):
    def __init__(self, platform: str, signatures: list[dict]) -> None:
        self.platform, self.signatures = platform, signatures

    def detect(self, url: str, html: str, headers: dict[str, str], dns_data: dict[str, list[str]], page: PageData, scripts: dict[str, str] | None = None) -> DetectionResult:
        host = urlparse(url).hostname or ""
        fields = {
            "domain": host, "html": html, "meta": f"{page.generator} {page.description}",
            "script": "\n".join(page.scripts), "asset": "\n".join(page.scripts + page.links),
            "javascript": page.inline_scripts + "\n" + "\n".join((scripts or {}).values()),
            "header": "\n".join(f"{k}: {v}" for k, v in headers.items()),
            "external_domain": "\n".join(page.external_domains),
            "dns": "\n".join(x for values in dns_data.values() for x in values),
        }
        evidence: list[Evidence] = []
        for sig in self.signatures:
            location = sig.get("type", "html"); haystack = fields.get(location, "")
            patterns = sig.get("pattern", []); patterns = [patterns] if isinstance(patterns, str) else patterns
            matched = []
            for pattern in patterns:
                ok = fnmatch.fnmatch(host, pattern) if location == "domain" else re.search(re.escape(str(pattern)), haystack, re.I) is not None
                if ok: matched.append(str(pattern))
            mode = sig.get("match", "any")
            if matched and (mode != "all" or len(matched) == len(patterns)):
                evidence.append(Evidence(sig["signature_name"], location, ", ".join(matched), int(sig.get("weight", 0))))
        score = min(100, sum(e.weight for e in evidence))
        return DetectionResult(self.platform if evidence else "unknown", score, score_class(score), evidence, needs_deep_scan=30 <= score < 80)

