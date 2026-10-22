"""Real released native LLMStream.collect and source usage."""

import asyncio

from _shared import FixtureLLM, Tracing, chat_context, native_job


async def main():
    tracing = Tracing("native-chat")
    try:
        with native_job():
            result = await FixtureLLM().chat(chat_ctx=chat_context()).collect()
            assert (
                result.text == "native LiveKit output"
                and result.usage.total_tokens == 18
            )
        print("native collect value and source counts preserved")
    finally:
        tracing.finish()


if __name__ == "__main__":
    asyncio.run(main())
