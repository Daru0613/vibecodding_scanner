from __future__ import annotations

import re
from urllib.parse import urlsplit

from core.models import PageData, ScanRecord

CHINA_SUFFIXES = (".cn", ".中国", ".公司", ".网络")
COMMON_CHINESE = re.compile(r"[的了一是在不有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经]")


def content_exclusion_reason(page: PageData, url: str) -> str:
    host = (urlsplit(url).hostname or "").lower().rstrip(".")
    lang = page.html_lang.replace("_", "-").lower()
    if host.endswith(CHINA_SUFFIXES):
        return "china-domain"
    if lang == "zh" or lang.startswith("zh-"):
        return "chinese-language"
    text = page.visible_text[:100_000]
    letters = [char for char in text if char.isalpha()]
    chinese_hits = len(COMMON_CHINESE.findall(text))
    hangul_hits = len(re.findall(r"[가-힣]", text))
    if len(letters) >= 80 and chinese_hits >= 12 and chinese_hits > hangul_hits * 3:
        return "chinese-language-likely"
    return ""


def is_high_confidence_vibe(record: ScanRecord) -> bool:
    if record.exclusion_reason or not (200 <= record.http_status < 400):
        return False
    if record.lovable_class in {"LOVABLE_CONFIRMED", "LOVABLE_PROBABLE"}:
        return True
    if record.builder in {"v0", "replit", "base44", "manus"} and record.builder_score >= 30:
        return True
    if record.claude_class != "CLAUDE_POSSIBLE":
        return False
    evidence = record.claude_evidence
    # Generic Tailwind/Lucide/layout combinations are useful research hints but
    # cannot establish Claude provenance. Export Claude-only rows only when a
    # direct public Artifact trace is present.
    return any(item.get("signature") == "claude_artifact" for item in evidence)
