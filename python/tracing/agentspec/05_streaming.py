"""Public synchronous/asynchronous message streams and actual zero usage."""

import asyncio

from _fixtures import build_agent, fixture_model
from _shared import build_respan, example_scope


async def main():
    respan = build_respan("streaming")
    with example_scope("streaming"):
        try:
            request = {"messages": [{"role": "user", "content": "stream fixture"}]}
            with fixture_model():
                sync = list(
                    build_agent("SyncStream").stream(request, stream_mode="messages")
                )
                asynchronous = [
                    value
                    async for value in build_agent("AsyncStream").astream(
                        request, stream_mode="messages"
                    )
                ]
            assert "".join(value[0].content for value in sync) == "fixture stream"
            assert (
                "".join(value[0].content for value in asynchronous) == "fixture stream"
            )
            print({"sync": "fixture stream", "async": "fixture stream"})
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
