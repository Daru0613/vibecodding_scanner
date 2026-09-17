import csv

from core.models import ScanRecord
from storage.csv_writer import CsvWriter


def test_compact_csv_schema_and_parent_creation(tmp_path):
    path = tmp_path / "results" / "csv" / "results.csv"
    writer = CsvWriter(str(path))
    writer.write(ScanRecord("id", "https://a.test", final_url="https://a.test/",
                            domain="a.test", lovable_class="LOVABLE_CONFIRMED"))
    writer.close()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert list(row) == [
        "site_url", "domain", "page_title", "source", "source_query",
        "source_seen_at", "http_status", "response_time_ms",
        "lovable_class", "lovable_evidence", "claude_class",
        "claude_evidence", "vibe_result", "framework",
        "needs_deep_scan", "error",
    ]
    assert row["site_url"] == "https://a.test/"
    assert row["lovable_class"] == "LOVABLE_CONFIRMED"
