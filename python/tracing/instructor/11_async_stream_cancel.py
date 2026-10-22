"""Native async iterable results and original cancellation behavior."""

import asyncio
import inspect

import instructor
from _respan_instructor import (
    User,
    attributes,
    create_respan_instructor_client,
    workflow,
)
from opentelemetry import trace


@workflow(name="instructor_example_11_async_stream_cancel")
async def execute(client):
    original = trace.get_current_span()
    response = client.create_iterable(
        response_model=User,
        messages=[{"role": "user", "content": "Extract Ada and Grace, both age36."}],
    )
    if inspect.isawaitable(response):
        response = await response
    assert trace.get_current_span() is original
    values = (
        [item.model_dump() async for item in response]
        if hasattr(response, "__aiter__")
        else [item.model_dump() for item in response]
    )
    error = asyncio.CancelledError("controlled fixture cancellation")

    async def cancelled(**kwargs):
        raise error

    custom = instructor.AsyncInstructor(client=None, create=cancelled)
    try:
        await custom.create(
            response_model=User,
            messages=[{"role": "user", "content": "Controlled cancellation."}],
            model="fixture-model",
        )
    except asyncio.CancelledError as caught:
        assert caught is error
    else:
        raise AssertionError("Original cancellation was swallowed")
    assert trace.get_current_span() is original
    return {"items": values, "cancellation_preserved": True}


async def main():
    tracing, client = create_respan_instructor_client(
        app_name="instructor-async-stream", async_client=True
    )
    try:
        with attributes("11_async_stream_cancel.py"):
            print(await execute(client))
    finally:
        await client.client.close()
        tracing.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
