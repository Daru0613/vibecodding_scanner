from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Candidate:
    url: str
    source: str
    source_query: str = ""
    source_seen_at: str = ""
    collected_at: str = ""
    url_type: str = "UNKNOWN"


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
    normalized_url: str = ""
    final_url: str = ""
    domain: str = ""
    http_status: int = 0
    content_type: str = ""
    content_length: int = 0
    http_date: str = ""
    http_last_modified: str = ""
    http_etag: str = ""
    source: str = ""
    source_query: str = ""
    source_seen_at: str = ""
    collected_at: str = ""
    checked_at: str = ""
    page_title: str = ""
    html_lang: str = ""
    korea_score: int = 0
    korea_class: str = "UNKNOWN"
    hangul_ratio: float = 0.0
    korea_evidence: list[str] = field(default_factory=list)
    lovable_class: str = "NO_LOVABLE_EVIDENCE"
    lovable_evidence: list[dict[str, Any]] = field(default_factory=list)
    claude_class: str = "NO_CLAUDE_EVIDENCE"
    claude_evidence: list[dict[str, Any]] = field(default_factory=list)
    vibe_result: str = "UNKNOWN"
    builder: str = "unknown"
    builder_score: int = 0
    builder_class: str = "UNKNOWN"
    builder_evidence: list[dict[str, Any]] = field(default_factory=list)
    framework: dict[str, Any] = field(default_factory=dict)
    libraries: list[str] = field(default_factory=list)
    external_domains: list[str] = field(default_factory=list)
    response_time: float = 0.0
    response_time_ms: float = 0.0
    scan_timestamp: str = ""
    needs_deep_scan: bool = False
    published_date: str = ""
    exclusion_reason: str = ""
    error: str = ""

    def csv_dict(self) -> dict[str, Any]:
        """Compact research-facing CSV; full detail remains available in JSONL/SQLite."""
        return {
            "site_url": self.final_url or self.normalized_url or self.original_url,
            "domain": self.domain,
            "page_title": self.page_title,
            "source": self.source,
            "source_query": self.source_query,
            "source_seen_at": self.source_seen_at,
            "http_status": self.http_status,
            "response_time_ms": self.response_time_ms,
            "lovable_class": self.lovable_class,
            "lovable_evidence": self.lovable_evidence,
            "claude_class": self.claude_class,
            "claude_evidence": self.claude_evidence,
            "vibe_result": self.vibe_result,
            "framework": self.framework,
            "needs_deep_scan": self.needs_deep_scan,
            "error": self.error,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
