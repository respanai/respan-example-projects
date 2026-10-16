"""Sync/async streaming and early close with released Agno SDK events."""

import asyncio

from _shared import build_agent, create_respan, example_attributes, print_result
from respan import workflow


@workflow(name="agno_07_streaming")
async def run_streaming():
    agent = build_agent(name="Stream Agent")
    sync_events = list(agent.run("hello", stream=True))
    async_events = [event async for event in agent.arun("hello", stream=True)]
    partial = agent.run("hello", stream=True)
    next(partial)
    partial.close()
    return {
        "sync": "".join(getattr(e, "content", "") or "" for e in sync_events),
        "async": "".join(getattr(e, "content", "") or "" for e in async_events),
        "partial_closed": True,
    }


def main():
    respan, _ = create_respan(app_name="agno-07-streaming")
    try:
        with example_attributes(respan, "agno_07_streaming"):
            result = asyncio.run(run_streaming())
        print_result("Streams", result)
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
