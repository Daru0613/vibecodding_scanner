from __future__ import annotations

import argparse
import asyncio
from types import SimpleNamespace

from main import run


if __name__ == "__main__":
    args = SimpleNamespace(limit=100, country=None, builder=None, output="test_results_100.csv", jsonl="test_results_100.jsonl", resume=False, max_concurrency=5, cache="test_cache.sqlite", settings="config/settings.yaml", signatures="config/signatures.yaml")
    summary = asyncio.run(run(args)); rows = summary["records"]
    count = lambda attr, value: sum(getattr(row, attr) == value for row in rows)
    print("\n=================================\n100 Site Test Result\n=================================")
    print(f"Candidate URLs       : {summary['candidates']}\nUnique URLs          : {summary['candidates']}\nSuccessfully Fetched : {sum(200 <= r.http_status < 400 for r in rows)}")
    print(f"KR Confirmed         : {count('korea_class', 'KR_CONFIRMED')}\nKR Possible          : {count('korea_class', 'KR_POSSIBLE')}")
    print(f"Vibe Confirmed       : {count('builder_class', 'CONFIRMED')}\nVibe Probable        : {count('builder_class', 'PROBABLE')}")
    print(f"Lovable              : {count('builder', 'lovable')}\nOther Builder         : {sum(r.builder not in ('lovable', 'unknown') for r in rows)}\nUnknown               : {count('builder', 'unknown')}")
    statuses = summary["statuses"]
    print(f"403                   : {statuses.get('403', 0)}\n429                   : {statuses.get('429', 0)}\nTimeout               : {sum('Timeout' in r.error for r in rows)}\nErrors                : {sum(bool(r.error) for r in rows)}")
    print(f"Total Requests        : {summary['requests']}\nTotal Runtime         : {summary['runtime']:.1f}s\n=================================")
