"""DSPy3.4 async ReActV2 with source tool IDs and complete tool results."""

import asyncio

import dspy
from _shared import FixtureLM, formatted, managed_example, traced_example


async def lookup(value: int) -> dict:
    return {"value": value, "vector": [float(i) for i in range(5000)]}


async def main():
    if not hasattr(dspy, "ReActV2"):
        print("SKIP: ReActV2 fixture requires DSPy3.4")
        return
    replies = [
        formatted(
            next_thought="Call lookup.",
            tool_calls={
                "tool_calls": [
                    {"id": "reactv2-lookup-id", "name": "lookup", "args": {"value": 2}}
                ]
            },
        ),
        formatted(
            next_thought="Submit the result.",
            tool_calls={
                "tool_calls": [
                    {
                        "id": "reactv2-submit-id",
                        "name": "submit",
                        "args": {"answer": "lookup completed"},
                    }
                ]
            },
        ),
    ]
    with managed_example(
        app_name="dspy-11-reactv2", example_name="11_react_v2"
    ) as context:
        with (
            traced_example(context),
            dspy.context(lm=FixtureLM(replies), adapter=dspy.ChatAdapter()),
        ):
            prediction = await dspy.ReActV2(
                "question -> answer", tools=[lookup], max_iters=2
            ).acall(question="lookup fixture")
            assert prediction.answer == "lookup completed"
        print("Async ReActV2 source IDs and complete tool results verified")


if __name__ == "__main__":
    asyncio.run(main())
