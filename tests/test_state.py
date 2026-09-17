from core.models import Candidate, ScanRecord
from core.state import CollectorState


def test_state_deduplicates_and_resumes(tmp_path):
    state = CollectorState(str(tmp_path / "collector.db"))
    items = [
        Candidate("https://Example.com/?utm_source=x", "seed", collected_at="2026-01-01T00:00:00Z"),
        Candidate("http://example.com", "ct", collected_at="2026-01-01T00:00:01Z"),
        Candidate("https://github.com/a/b", "github", collected_at="2026-01-01T00:00:02Z"),
    ]
    added, excluded = state.add_candidates(items)
    assert (added, excluded) == (1, 1)
    pending = state.pending()
    assert len(pending) == 1 and pending[0].source == "seed"
    record = ScanRecord("id", pending[0].url, normalized_url="https://example.com/",
                        final_url="https://example.com/", checked_at="2026-01-01T00:01:00Z")
    state.complete(pending[0], record, True)
    assert state.pending() == []
    assert state.counts() == {"total": 1, "completed": 1, "pending": 0}
    state.close()


def test_redirect_final_is_detected_as_duplicate(tmp_path):
    state = CollectorState(str(tmp_path / "collector.db"))
    first = Candidate("https://a.example", "seed", collected_at="now")
    state.add_candidates([first])
    record = ScanRecord("id", first.url, normalized_url="https://a.example/",
                        final_url="https://final.example/", checked_at="now")
    state.complete(first, record, True)
    assert state.has_scanned_final("https://final.example/?utm_source=x")
    state.close()
