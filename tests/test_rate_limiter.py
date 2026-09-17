import asyncio
import pytest
from core.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_per_domain_serializes():
    limiter = RateLimiter(5, 1); active = 0; maximum = 0
    async def job():
        nonlocal active, maximum
        async with limiter.limit("x"):
            active += 1; maximum = max(maximum, active); await asyncio.sleep(.01); active -= 1
    await asyncio.gather(job(), job())
    assert maximum == 1

