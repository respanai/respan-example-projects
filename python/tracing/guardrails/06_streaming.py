"""Consume synchronous and asynchronous native Guardrails fixture streams."""

import asyncio

from _shared import example_attributes, local_guard, make_respan, result_summary
from guardrails import AsyncGuard, Guard
from pydantic import BaseModel
from respan import workflow

WORKFLOW_NAME = "guardrails_streaming_workflow"


class Reply(BaseModel):
    answer: str


@workflow(name=WORKFLOW_NAME)
async def run_example():
    kwargs = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Return a streaming fixture"}],
        "mock_response": '{"answer":"Streamed fixture reply"}',
        "stream": True,
        "num_reasks": 0,
    }
    sync_chunks = list(local_guard(Guard.for_pydantic(Reply))(**kwargs))
    async_stream = await local_guard(AsyncGuard.for_pydantic(Reply))(**kwargs)
    async_chunks = [chunk async for chunk in async_stream]
    assert sync_chunks[-1].validation_passed and async_chunks[-1].validation_passed
    return {
        "sync": result_summary(sync_chunks[-1]),
        "async": result_summary(async_chunks[-1]),
    }


async def main():
    respan, _ = make_respan(WORKFLOW_NAME)
    try:
        with example_attributes("streaming", WORKFLOW_NAME):
            print(await run_example())
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
