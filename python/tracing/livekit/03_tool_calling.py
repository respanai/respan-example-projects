"""Two actual declarations/executions, full schemas, history and vectors."""

import asyncio

from _shared import FixtureLLM, Tracing, chat_context, native_job, vector_tool
from livekit.agents import llm


async def main():
    tracing = Tracing("full-tool-payloads")
    try:
        with native_job():
            response = (
                await FixtureLLM(scenario="tools")
                .chat(chat_ctx=chat_context(True), tools=[vector_tool])
                .collect()
            )
            results = [
                await llm.execute_function_call(call, llm.ToolContext([vector_tool]))
                for call in response.tool_calls
            ]
            assert len(results) == 2 and all(
                len(r.raw_output["dense"]) == 5000
                and len(r.raw_output["sparse"]) == 256
                for r in results
            )
        print("actual tools:2; dense:5000; sparse:256; schema properties:123")
    finally:
        tracing.finish()


if __name__ == "__main__":
    asyncio.run(main())
