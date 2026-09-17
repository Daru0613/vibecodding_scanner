from core.cache import ResponseCache
from core.models import FetchResult

def test_cache(tmp_path):
    cache = ResponseCache(str(tmp_path / "c.sqlite")); cache.put(FetchResult("https://a", status=200, body="x"))
    hit = cache.get("https://a"); cache.close()
    assert hit and hit.status == 200 and hit.from_cache

