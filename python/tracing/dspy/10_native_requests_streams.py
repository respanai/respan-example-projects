"""DSPy3.4 native request/response and streamify with actual fixture usage."""

import asyncio

import dspy
from _shared import formatted, managed_example, native_model, traced_example


async def main():
    if not hasattr(dspy, "lm15"):
        print("SKIP: native lm15 engine fixture requires DSPy3.4")
        return
    from dspy.lm15 import FunctionTool, Message, Request, Response, ToolCallPart, Usage

    native = Response(
        id="fixture-native-response",
        model="fixture-dspy",
        message=Message.assistant(
            [
                ToolCallPart(
                    id="fixture-native-tool-id", name="lookup", input={"value": 2}
                )
            ]
        ),
        finish_reason="tool_call",
        usage=Usage(
            input_tokens=11,
            output_tokens=7,
            total_tokens=18,
            cache_read_tokens=3,
            reasoning_tokens=2,
        ),
    )
    streamed = Response(
        id="fixture-stream-response",
        model="fixture-dspy",
        message=Message.assistant(formatted(answer="streamed fixture")),
        finish_reason="stop",
        usage=Usage(input_tokens=4, output_tokens=2, total_tokens=6),
    )
    with managed_example(
        app_name="dspy-10-native", example_name="10_native_requests_streams"
    ) as context:
        with traced_example(context):
            lm = native_model([native, streamed])
            request = Request(
                model="openai/fixture-dspy",
                messages=(Message.user("lookup fixture"),),
                tools=(
                    FunctionTool(
                        name="lookup",
                        parameters={
                            "type": "object",
                            "properties": {"value": {"type": "integer"}},
                        },
                    ),
                ),
            )
            with dspy.context(lm=lm, disable_history=True):
                assert lm(request) is native
                outputs = [
                    item
                    async for item in dspy.streamify(
                        dspy.Predict("question -> answer")
                    )(question="stream fixture")
                ]
                assert outputs[-1].answer == "streamed fixture"
        print(
            "Native response identity, tool ID, usage and streamed Prediction verified"
        )


if __name__ == "__main__":
    asyncio.run(main())
