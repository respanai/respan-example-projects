"""Consume, close, fail and cancel native ResponseStreams without provider calls."""

import asyncio

from _shared import (
    create_respan,
    create_streaming_fixture_client,
    finish_respan,
    workflow_attributes,
)
from agent_framework import Content, Message, ResponseStream
from respan import Respan, workflow

WORKFLOW_NAME = "microsoft-agent-framework-stream-lifecycle"


@workflow(name=WORKFLOW_NAME)
async def run_example():
    outcomes = []
    for mode in ("complete", "close", "error", "cancel"):
        client = create_streaming_fixture_client(mode)
        stream = client.get_response(
            [Message("user", [Content.from_text("Fixture streaming prompt")])],
            stream=True,
        )
        assert isinstance(stream, ResponseStream)
        await anext(stream)
        if mode == "cancel":
            pending = asyncio.create_task(anext(stream))
            await asyncio.sleep(0)
            pending.cancel()
            try:
                await pending
            except asyncio.CancelledError:
                pass
            else:
                raise AssertionError("Expected cancellation")
        elif mode == "error":
            try:
                await anext(stream)
            except RuntimeError as exc:
                assert "Controlled fixture" in str(exc)
            else:
                raise AssertionError("Expected stream failure")
        elif mode == "close":
            await stream.close()
        else:
            async for _ in stream:
                pass
            assert (await stream.get_final_response()).text == "Fixture answer"
        assert client.closed
        outcomes.append(mode)
    return {"completed_modes": outcomes}


async def main():
    respan = create_respan(WORKFLOW_NAME)
    try:
        with Respan.propagate_attributes(**workflow_attributes(WORKFLOW_NAME)):
            print(await run_example())
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
