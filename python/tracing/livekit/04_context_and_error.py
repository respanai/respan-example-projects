"""Native returned tool error and actual HTTP429; no invented output/status."""

import asyncio

from _shared import APIConnectOptions, Tracing, chat_context, native_job, provider_model
from livekit.agents import llm
from livekit.agents._exceptions import APIStatusError


async def main():
    tracing = Tracing("expected-errors")
    model, client = provider_model(error=True)
    try:
        with native_job():
            result = await llm.execute_function_call(
                llm.FunctionToolCall(
                    name="missing_tool", call_id="actual-error", arguments="{}"
                ),
                llm.ToolContext([]),
            )
            assert result.fnc_call_out.is_error and isinstance(
                result.raw_exception, ValueError
            )
            try:
                await model.chat(
                    chat_ctx=chat_context(), conn_options=APIConnectOptions(max_retry=0)
                ).collect()
            except APIStatusError as error:
                assert error.status_code == 429
            else:
                raise AssertionError("native SDK error missing")
        print("native error result and HTTP429 preserved")
    finally:
        await client.close()
        await model.aclose()
        tracing.finish()


if __name__ == "__main__":
    asyncio.run(main())
