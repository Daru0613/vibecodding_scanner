import yaml
from core.models import PageData
from core.parser import parse_html
from fingerprint.engine import FingerprintEngine

def engine():
    return FingerprintEngine(yaml.safe_load(open("config/signatures.yaml", encoding="utf-8")))

def test_lovable_pair_detection():
    html = '<script src="/~flock.js" data-proxy-url="/~api/analytics"></script>'
    result = engine().detect("https://x.example", html, {}, {}, parse_html(html, "https://x.example"))
    assert result.builder == "lovable" and result.score == 40

def test_generic_vite_not_lovable():
    html = '<script src="/assets/index-abcd.js"></script>'
    result = engine().detect("https://x.example", html, {}, {}, parse_html(html, "https://x.example"))
    assert result.builder == "unknown" and result.framework["framework"] == "vite"

def test_score_combines_evidence():
    html = '<script src="/~flock.js" data-proxy-url="/~api/analytics"></script>'
    result = engine().detect("https://x.lovable.app", html, {}, {}, parse_html(html, "https://x.lovable.app"))
    assert result.score == 90 and result.classification == "CONFIRMED"

def test_claude_style_is_independent_from_lovable():
    classes = "flex grid text-xl bg-white rounded-lg px-4 py-2 gap-4 max-w-lg tracking-wide"
    html = f'''<!-- HEADER --><!-- HERO --><!-- FEATURES --><!-- CTA -->
    <main class="{classes}"><section>hero features cards dashboard</section>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"></svg></main>'''
    results = engine().detect_all("https://x.example", html, {}, {}, parse_html(html, "https://x.example"))
    assert results["claude"].evidence
    assert results["lovable"].evidence == []

