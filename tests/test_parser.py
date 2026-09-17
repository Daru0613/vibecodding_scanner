from core.parser import parse_html

def test_html_parser_excludes_script_text():
    page = parse_html('<html lang="ko"><head><title>T</title></head><body>보이는 글<script>숨은글</script></body></html>', "https://a.test")
    assert page.title == "T" and "보이는" in page.visible_text and "숨은글" not in page.visible_text

def test_published_date_from_public_metadata():
    page = parse_html('<meta property="article:published_time" content="2026-01-02T03:04:05+09:00">', "https://a.test")
    assert page.published_date == "2026-01-02T03:04:05+09:00"
