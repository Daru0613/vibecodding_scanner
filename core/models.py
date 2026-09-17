from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Evidence:
    signature: str
    location: str
    value: str
    weight: int = 0


@dataclass
class FetchResult:
    original_url: str
    final_url: str = ""
    status: int = 0
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    content_type: str = ""
    content_length: int = 0
    response_time: float = 0.0
    redirect_count: int = 0
    error: str = ""
    from_cache: bool = False


@dataclass
class DetectionResult:
    builder: str = "unknown"
    score: int = 0
    classification: str = "UNKNOWN"
    evidence: list[Evidence] = field(default_factory=list)
    framework: dict[str, Any] = field(default_factory=dict)
    ai_style_score: int = 0
    needs_deep_scan: bool = False


@dataclass
class PageData:
    title: str = ""
    description: str = ""
    generator: str = ""
    html_lang: str = ""
    scripts: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    external_domains: list[str] = field(default_factory=list)
    visible_text: str = ""
    inline_scripts: str = ""
    published_date: str = ""


@dataclass
class ScanRecord:
    site_id: str
    original_url: str
    final_url: str = ""
    domain: str = ""
    http_status: int = 0
    page_title: str = ""
    html_lang: str = ""
    korea_score: int = 0
    korea_class: str = "NON_KR_OR_UNKNOWN"
    hangul_ratio: float = 0.0
    builder: str = "unknown"
    builder_score: int = 0
    builder_class: str = "UNKNOWN"
    builder_evidence: list[dict[str, Any]] = field(default_factory=list)
    framework: dict[str, Any] = field(default_factory=dict)
    external_domains: list[str] = field(default_factory=list)
    response_time: float = 0.0
    scan_timestamp: str = ""
    needs_deep_scan: bool = False
    published_date: str = ""
    error: str = ""

    def csv_dict(self) -> dict[str, Any]:
        """Human-facing CSV fields first, followed by research/audit detail."""
        platform = {
            "claude": "Claude",
            "lovable": "Lovable",
            "v0": "Other AI (v0)",
            "replit": "Other AI (Replit)",
            "base44": "Other AI (Base44)",
            "manus": "Other AI (Manus)",
            "unknown": "Unknown",
        }.get(self.builder, f"Other AI ({self.builder})")
        return {
            "바이브코딩 유추 플랫폼": platform,
            "링크": self.final_url or self.original_url,
            "바이브코딩 의심 점수": self.builder_score,
            "취약점": "NOT_SCANNED",
            "취약한 데이터": "",
            "게시날짜": self.published_date,
            **asdict(self),
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
