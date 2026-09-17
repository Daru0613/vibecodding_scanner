import io

from core.progress import ProgressReporter, _bar, _duration


def test_progress_bar_and_duration():
    assert _bar(5, 10, 10) == "[#####-----]"
    assert _duration(65) == "01:05"
    assert _duration(3661) == "01:01:01"


def test_scan_progress_contains_percent_counts_and_eta():
    stream = io.StringIO()
    reporter = ProgressReporter(stream)
    reporter.start_scan(2)
    reporter.scan(200, True)
    reporter.scan(0, False, "TimeoutException")
    output = stream.getvalue()
    assert "50.0%" in output
    assert "100.0%" in output
    assert "2/2" in output
    assert "Saved 1" in output
    assert "Errors 1" in output
    assert "ETA" in output
