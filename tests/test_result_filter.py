from core.models import PageData, ScanRecord
from filter.result_filter import content_exclusion_reason, is_high_confidence_vibe


def record(**kwargs):
    defaults = {
        "site_id": "id", "original_url": "https://example.com",
        "final_url": "https://example.com/", "http_status": 200,
    }
    defaults.update(kwargs)
    return ScanRecord(**defaults)


def test_video_like_weak_claude_signal_is_not_exported():
    row = record(
        claude_class="CLAUDE_POSSIBLE",
        claude_evidence=[{"signature": "ai_ui_structure", "weight": 5}],
    )
    assert not is_high_confidence_vibe(row)


def test_multiple_generic_claude_style_signals_are_not_exported():
    row = record(
        claude_class="CLAUDE_POSSIBLE",
        claude_evidence=[
            {"signature": "tailwind_utility_density", "weight": 10},
            {"signature": "section_labeled_comments", "weight": 10},
        ],
    )
    assert not is_high_confidence_vibe(row)


def test_direct_claude_artifact_trace_is_exported():
    row = record(
        claude_class="CLAUDE_POSSIBLE",
        claude_evidence=[{"signature": "claude_artifact", "weight": 50}],
    )
    assert is_high_confidence_vibe(row)


def test_lovable_is_exported_unless_content_is_excluded():
    assert is_high_confidence_vibe(record(lovable_class="LOVABLE_CONFIRMED"))
    assert not is_high_confidence_vibe(
        record(lovable_class="LOVABLE_CONFIRMED", exclusion_reason="chinese-language")
    )


def test_chinese_domain_and_language_are_excluded():
    assert content_exclusion_reason(PageData(), "https://example.cn") == "china-domain"
    assert content_exclusion_reason(PageData(html_lang="zh-CN"), "https://example.com") == "chinese-language"
