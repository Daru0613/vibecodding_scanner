from __future__ import annotations

from core.models import DetectionResult, PageData
from fingerprint.configurable import ConfigurableDetector
from fingerprint.generic import GenericDetector
from core.models import Evidence
import re


class FingerprintEngine:
    def __init__(self, config: dict) -> None:
        grouped: dict[str, list[dict]] = {}
        for sig in config.get("signatures", []): grouped.setdefault(sig["platform"], []).append(sig)
        self.detectors = {name: ConfigurableDetector(name, values) for name, values in grouped.items()}
        self.generic = GenericDetector()

    def detect(self, url: str, html: str, headers: dict[str, str], dns_data: dict[str, list[str]], page: PageData, scripts: dict[str, str] | None = None) -> DetectionResult:
        results = list(self.detect_all(url, html, headers, dns_data, page, scripts).values())
        best = max(results, key=lambda x: x.score, default=DetectionResult())
        best.framework = self.generic.detect(url, html, headers, dns_data, page, scripts).framework
        return best

    def detect_all(self, url: str, html: str, headers: dict[str, str], dns_data: dict[str, list[str]], page: PageData, scripts: dict[str, str] | None = None) -> dict[str, DetectionResult]:
        results = {name: detector.detect(url, html, headers, dns_data, page, scripts)
                   for name, detector in self.detectors.items()}
        claude = results.setdefault("claude", DetectionResult())
        claude_evidence = list(claude.evidence)
        utility_hits = re.findall(r'(?<![\w-])(?:flex|grid|text-[\w-]+|bg-[\w-]+|rounded-[\w-]*|p[xy]-\d+|gap-\d+|max-w-[\w-]+|tracking-[\w-]+)(?![\w-])', html, re.I)
        if len(set(x.lower() for x in utility_hits)) >= 8:
            claude_evidence.append(Evidence("tailwind_utility_density", "html", f"{len(utility_hits)} utility occurrences", 10))
        if all(token in html for token in ('viewBox="0 0 24 24"', 'fill="none"', 'stroke="currentColor"')):
            claude_evidence.append(Evidence("lucide_svg_style", "html", "24x24/currentColor SVG", 5))
        labels = re.findall(r'<!--\s*(HEADER|NAV|HERO|FEATURES|CTA|FOOTER)\s*-->', html, re.I)
        if len(set(x.upper() for x in labels)) >= 3:
            claude_evidence.append(Evidence("section_labeled_comments", "html", ", ".join(sorted(set(labels))), 10))
        structure = sum(bool(re.search(term, html, re.I)) for term in ("hero", "features", "cta", "cards", "navigation", "footer", "how it works", "dashboard"))
        if structure >= 4:
            claude_evidence.append(Evidence("ai_ui_structure", "html", f"{structure} common sections", 5))
        heuristic_score = min(29, sum(e.weight for e in claude_evidence if e.signature != "claude_artifact"))
        direct_score = sum(e.weight for e in claude_evidence if e.signature == "claude_artifact")
        score = min(100, heuristic_score + direct_score)
        results["claude"] = DetectionResult("claude" if claude_evidence else "unknown", score,
                                             "POSSIBLE" if claude_evidence else "UNKNOWN",
                                             claude_evidence, needs_deep_scan=bool(claude_evidence))
        return results

