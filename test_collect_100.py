"""Real-network collection test (500-site target); not collected by pytest."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from main import run

__test__ = False


if __name__ == "__main__":
    args = SimpleNamespace(
        limit=500, source=None, country=None, builder=None,
        output="results/csv/test_results_500.csv",
        jsonl="results/jsonl/test_results_500.jsonl",
        resume=False, concurrency=5, database="test_collector.db",
        settings="config/settings.yaml", signatures="config/signatures.yaml",
    )
    asyncio.run(run(args))
