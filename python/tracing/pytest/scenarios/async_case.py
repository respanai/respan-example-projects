import asyncio

import pytest


@pytest.mark.asyncio
async def test_native_async():
    await asyncio.sleep(0)
    assert 2 + 3 == 5
