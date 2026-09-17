from __future__ import annotations

from core.models import DetectionResult, PageData
from fingerprint.configurable import ConfigurableDetector
from fingerprint.generic import GenericDetector


class FingerprintEngine:
    def __init__(self, config: dict) -> None:
        grouped: dict[str, list[dict]] = {}
        for sig in config.get("signatures", []): grouped.setdefault(sig["platform"], []).append(sig)
        self.detectors = [ConfigurableDetector(name, values) for name, values in grouped.items()]
        self.generic = GenericDetector()

    def detect(self, url: str, html: str, headers: dict[str, str], dns_data: dict[str, list[str]], page: PageData, scripts: dict[str, str] | None = None) -> DetectionResult:
        results = [x.detect(url, html, headers, dns_data, page, scripts) for x in self.detectors]
        best = max(results, key=lambda x: x.score, default=DetectionResult())
        best.framework = self.generic.detect(url, html, headers, dns_data, page, scripts).framework
        return best

