from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager


class RateLimiter:
    def __init__(self, global_limit: int = 10, per_domain: int = 1) -> None:
        self.global_sem = asyncio.Semaphore(global_limit)
        self.domain_sems: dict[str, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(per_domain))

    @asynccontextmanager
    async def limit(self, domain: str):
        async with self.global_sem, self.domain_sems[domain]:
            yield

