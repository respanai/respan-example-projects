"""Observe real DSPy async model/module/tool callbacks with controlled responses."""

import asyncio

import dspy
from _shared import managed_example, print_result, traced_example


async def main():
    with managed_example(
        app_name="dspy-07-async", example_name="07_async_calls"
    ) as context:

        async def echo(value: str) -> str:
            await asyncio.sleep(0)
            return value

        with traced_example(context):
            result = await dspy.Predict("question -> answer").acall(
                question="async fixture"
            )
            assert result.answer == "async fixture"
            assert await dspy.Tool(echo).acall(value="async tool") == "async tool"
        print_result("Answer", result.answer)


if __name__ == "__main__":
    asyncio.run(main())
