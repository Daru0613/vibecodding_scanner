from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from core.models import PageData

HANGUL = re.compile(r"[가-힣]")
PHONE = re.compile(r"(?:^|\D)(?:010-?\d{3,4}-?\d{4}|0(?:2|31|32|51|53|62)-?\d{3,4}-?\d{4})(?:\D|$)")
ADDRESS = re.compile(r"서울특별시|서울시|경기도|부산광역시|인천광역시|대구광역시|대전광역시|광주광역시|울산광역시|세종특별자치시|제주특별자치도|\S+(?:시|군|구)\s+\S+(?:로|길|동)")
MONEY = re.compile(r"(?:₩|원|만원)")
ORG = re.compile(r"대학교|고등학교|중학교|초등학교|주식회사|동아리|학생회|학과|학부|교내|공공기관")


@dataclass
class KoreaResult:
    score: int
    classification: str
    hangul_ratio: float
    evidence: list[str] = field(default_factory=list)


def classify_korea(page: PageData, url: str, settings: dict) -> KoreaResult:
    cfg = settings.get("korea", {})
    text = page.visible_text
    letters = [c for c in text if c.isalpha()]
    ratio = len(HANGUL.findall(text)) / max(1, len(letters))
    score = 0; evidence: list[str] = []
    def add(points: int, reason: str):
        nonlocal score; score += points; evidence.append(reason)
    if page.html_lang.startswith("ko"): add(3, "html lang=ko")
    if ratio >= float(cfg.get("hangul_ratio", 0.15)): add(3, f"hangul ratio={ratio:.3f}")
    if PHONE.search(text): add(2, "Korean phone pattern")
    if ADDRESS.search(text): add(2, "Korean address pattern")
    if MONEY.search(text): add(1, "Korean currency")
    if ORG.search(text): add(1, "Korean organization term")
    if (urlparse(url).hostname or "").endswith(".kr"): add(1, ".kr domain")
    confirmed = int(cfg.get("confirmed", 5)); possible = int(cfg.get("possible", 3))
    label = "KR_CONFIRMED" if score >= confirmed else "KR_POSSIBLE" if score >= possible else "NON_KR_OR_UNKNOWN"
    return KoreaResult(score, label, ratio, evidence)

