from __future__ import annotations

from abc import ABC, abstractmethod


class Collector(ABC):
    @abstractmethod
    async def collect(self, limit: int) -> list[str]: ...

