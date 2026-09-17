from __future__ import annotations

import asyncio
import dns.asyncresolver


async def lookup(hostname: str, include_lovable_txt: bool = True) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"A": [], "AAAA": [], "CNAME": [], "TXT": [], "LOVABLE_TXT": []}
    async def one(name: str, kind: str, key: str | None = None):
        try:
            answers = await dns.asyncresolver.resolve(name, kind, lifetime=4)
            result[key or kind] = [str(x).strip('"') for x in answers]
        except Exception: pass
    await asyncio.gather(*(one(hostname, k) for k in ("A", "AAAA", "CNAME", "TXT")))
    if include_lovable_txt: await one(f"_lovable.{hostname}", "TXT", "LOVABLE_TXT")
    return result
