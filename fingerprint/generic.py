from __future__ import annotations

from core.models import DetectionResult, PageData
from fingerprint.base import FingerprintDetector


class GenericDetector(FingerprintDetector):
    platform = "generic"
    def detect(self, url: str, html: str, headers: dict[str, str], dns_data: dict[str, list[str]], page: PageData, scripts: dict[str, str] | None = None) -> DetectionResult:
        blob = (html + " " + " ".join(page.scripts)).lower()
        framework: dict[str, str | bool] = {}
        if "/_next/static/" in blob or "__next_data__" in blob: framework["framework"] = "next.js"
        elif "/assets/index-" in blob or "@vite" in blob: framework["framework"] = "vite"
        elif "react" in blob: framework["framework"] = "react"
        if "tailwind" in blob: framework["css"] = "tailwind"
        if "tanstack" in blob: framework["router"] = "tanstack"
        if "supabase" in blob: framework["backend"] = "supabase"
        if "firebase" in blob: framework["firebase"] = True
        if 'stroke="currentcolor"' in blob and 'viewbox="0 0 24 24"' in blob: framework["icons"] = "lucide-style"
        return DetectionResult(framework=framework)

