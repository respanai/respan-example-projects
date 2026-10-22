"""Native iteration, early close and caller context remain unchanged."""

import asyncio

from _shared import FixtureLLM, Tracing, chat_context, native_job
from opentelemetry import trace


async def main():
    tracing = Tracing("streaming-and-close")
    try:
        with native_job() as parent:
            stream = FixtureLLM().chat(chat_ctx=chat_context())
            assert stream.__aiter__() is stream
            pieces = [
                chunk.delta.content or "" async for chunk in stream if chunk.delta
            ]
            text = "".join(pieces)
            assert text == "native LiveKit output"
            assert trace.get_current_span() is parent
            early = FixtureLLM(finish=asyncio.Event()).chat(chat_ctx=chat_context())
            first = await early.__anext__()
            assert first.delta.content == "native "
            assert await early.aclose() is None
            assert trace.get_current_span() is parent
        print("native stream and early close preserved")
    finally:
        tracing.finish()


if __name__ == "__main__":
    asyncio.run(main())
