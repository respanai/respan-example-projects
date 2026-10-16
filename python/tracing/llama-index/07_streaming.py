"""Consume the native synchronous and asynchronous chat generators."""

import asyncio

from _shared import build_llm, create_respan, print_result, traced_example
from llama_index.core.llms import ChatMessage


async def main() -> None:
    context = create_respan(
        app_name="llama-index-streaming", example_name="07_streaming"
    )
    llm = build_llm(context.settings)
    with traced_example(
        context,
        root_span_name=context.example_name,
        input_data={"request": "stream tracing tip"},
    ) as root:
        sync_result = list(
            llm.stream_chat([ChatMessage(role="user", content="Give a tracing tip.")])
        )[-1]
        stream = await llm.astream_chat(
            [ChatMessage(role="user", content="Give another tracing tip.")]
        )
        async_result = None
        async for result in stream:
            async_result = result
        assert async_result is not None
        root.set_output({"sync": str(sync_result), "async": str(async_result)})
    print_result("Streaming completed", True)


if __name__ == "__main__":
    asyncio.run(main())
