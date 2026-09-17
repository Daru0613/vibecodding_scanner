from __future__ import annotations

from abc import ABC, abstractmethod

from core.models import DetectionResult, PageData


class FingerprintDetector(ABC):
    platform = "unknown"
    @abstractmethod
    def detect(self, url: str, html: str, headers: dict[str, str], dns_data: dict[str, list[str]], page: PageData, scripts: dict[str, str] | None = None) -> DetectionResult: ...

