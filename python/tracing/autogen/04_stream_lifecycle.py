"""Completion, explicit close, provider read error and cancellation."""

import asyncio

from _shared import StreamFixture, client, httpx, run
from autogen_core.models import UserMessage
from openai import APIConnectionError


async def scenario():
    for mode in ("complete", "close", "error", "cancel"):
        fixture = StreamFixture(mode)
        model = await client(stream=fixture)
        stream = model.create_stream(
            [UserMessage(content=f"Fixture {mode} stream.", source="user")]
        )
        assert await anext(stream) == "Fixture "
        if mode == "close":
            await stream.aclose()
        elif mode == "error":
            try:
                await anext(stream)
            except (httpx.ReadError, APIConnectionError):
                pass
            else:
                raise AssertionError("Expected stream failure")
        elif mode == "cancel":
            task = asyncio.create_task(anext(stream))
            await fixture.waiting.wait()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        else:
            events = [event async for event in stream]
            assert events[-1].content == "Fixture stream answer."
    return "All four stream lifecycle paths verified."


if __name__ == "__main__":
    run("stream-lifecycle", scenario)
