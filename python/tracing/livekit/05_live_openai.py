"""Actual released OpenAI companion over controlled HTTP; optional live model."""

import asyncio
import os

from _shared import APIConnectOptions, Tracing, chat_context, native_job, provider_model


async def main():
    live = os.getenv("RESPAN_LIVEKIT_LIVE", "0") == "1"
    tracing = Tracing("openai-companion")
    model, client = provider_model(live=live)
    try:
        with native_job():
            result = await model.chat(
                chat_ctx=chat_context(), conn_options=APIConnectOptions(max_retry=0)
            ).collect()
            assert result.text
        print("real released OpenAI companion completed; live=" + str(live))
    finally:
        await client.close()
        await model.aclose()
        tracing.finish()


if __name__ == "__main__":
    asyncio.run(main())
