from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from core.models import Candidate


def candidate(url: str, source: str, query: str = "", seen_at: str = "") -> Candidate:
    return Candidate(url=url, source=source, source_query=query, source_seen_at=seen_at,
                     collected_at=datetime.now(timezone.utc).isoformat())


class Collector(ABC):
    @abstractmethod
    async def collect(self, limit: int) -> list[Candidate]: ...

