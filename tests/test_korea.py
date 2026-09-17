from core.models import PageData
from filter.korea_relevance import classify_korea

SETTINGS = {"korea": {"confirmed": 5, "possible": 3, "hangul_ratio": .15}}

def test_korea_score_visible_text():
    page = PageData(html_lang="ko", visible_text="서울특별시에서 운영하는 대학교입니다. 전화 02-123-4567")
    result = classify_korea(page, "https://example.com", SETTINGS)
    assert result.classification == "KR_CONFIRMED" and result.score >= 5

def test_script_not_part_of_ratio():
    page = PageData(visible_text="hello world", inline_scripts="한글" * 100)
    assert classify_korea(page, "https://example.com", SETTINGS).hangul_ratio == 0

