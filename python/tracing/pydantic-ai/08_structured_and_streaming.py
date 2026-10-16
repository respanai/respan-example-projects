"""Released PydanticAI structured output and async stream success/failure."""

import asyncio

from _gateway import finish_respan, make_respan
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel
from respan import workflow


class Answer(BaseModel):
    value: int


async def stream(messages, info):
    yield "stream "
    yield "answer"


async def failed_stream(messages, info):
    yield "partial "
    raise RuntimeError("expected stream model failure")


@workflow(name="pydantic_ai_structured_and_streaming")
async def run_features():
    result = await Agent(
        TestModel(custom_output_args={"value": 42}),
        output_type=Answer,
        name="structured_answer",
    ).run("Return the structured answer")
    assert result.output.value == 42
    async with Agent(
        FunctionModel(stream_function=stream), name="stream_answer"
    ).run_stream("Stream the response") as result:
        chunks = [chunk async for chunk in result.stream_text()]
    assert chunks[-1] == "stream answer"
    try:
        async with Agent(
            FunctionModel(stream_function=failed_stream), name="stream_failure"
        ).run_stream("Demonstrate a controlled failure") as result:
            async for _chunk in result.stream_text():
                pass
    except RuntimeError as error:
        assert str(error) == "expected stream model failure"
    else:
        raise AssertionError("Expected the local stream failure")
    return {"structured_value": 42, "stream": chunks[-1], "expected_error": True}


def main():
    respan = None
    try:
        respan = make_respan("structured-streaming", version=6)
        print(asyncio.run(run_features()))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    main()
