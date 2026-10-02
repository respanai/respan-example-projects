from __future__ import annotations

import asyncio

from _shared import clients, example_attributes, finish, make_respan
from respan import workflow

EXAMPLE = "streaming-async"


@workflow(name="exa_python_streaming_async")
async def streaming_calls(sync_client, async_client):
    search_text = "".join(
        chunk.content or ""
        for chunk in sync_client.stream_search("stream a grounded search", type="auto")
    )
    async_search = await async_client.search(
        "async Exa search",
        num_results=1,
        contents={"highlights": True},
    )
    answer_stream = await async_client.stream_answer("stream an Exa answer")
    answer_text = "".join([chunk.content or "" async for chunk in answer_stream])
    return search_text, async_search.results[0].url, answer_text


def main() -> None:
    respan = make_respan(EXAMPLE)
    try:
        with (
            clients() as (sync_client, async_client, mode),
            example_attributes(EXAMPLE, mode) as workflow_name,
        ):
            result = asyncio.run(streaming_calls(sync_client, async_client))
            print({"workflow_name": workflow_name, "mode": mode, "result": result})
    finally:
        finish(respan)


if __name__ == "__main__":
    main()
