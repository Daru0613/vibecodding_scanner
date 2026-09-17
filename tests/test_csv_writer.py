import csv
from core.models import ScanRecord
from storage.csv_writer import CsvWriter

def test_required_korean_columns_are_first(tmp_path):
    path = tmp_path / "results.csv"
    writer = CsvWriter(str(path))
    writer.write(ScanRecord("id", "https://a.test", builder="lovable", builder_score=85, published_date="2026-01-02"))
    writer.close()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert list(row)[:6] == ["바이브코딩 유추 플랫폼", "링크", "바이브코딩 의심 점수", "취약점", "취약한 데이터", "게시날짜"]
    assert row["바이브코딩 유추 플랫폼"] == "Lovable"
    assert row["취약점"] == "NOT_SCANNED"
