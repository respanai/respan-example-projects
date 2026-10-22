from __future__ import annotations

import asyncio

from _shared import (
    example_attributes,
    make_client,
    make_respan,
    model_name,
    print_result,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "async-stream-content"


@workflow(name=workflow_name(EXAMPLE_NAME))
async def stream_content() -> str:
    client = make_client()
    try:
        stream = await client.aio.models.generate_content_stream(
            model=model_name(), contents="One concise sentence about tracing."
        )
        return "".join([chunk.text or "" async for chunk in stream])
    finally:
        await client.aio.aclose()
        client.close()


def main() -> None:
    respan = make_respan(EXAMPLE_NAME)
    try:
        with example_attributes(EXAMPLE_NAME) as identifier:
            print_result(EXAMPLE_NAME, identifier, asyncio.run(stream_content()))
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
