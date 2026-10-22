"""Assistant text and structured output through the released SDK."""

from _shared import client, response, run
from autogen_agentchat.agents import AssistantAgent
from pydantic import BaseModel


class Answer(BaseModel):
    value: int


async def scenario():
    model = await client(response("Hello from AutoGen."), response('{"value":0}'))
    result = await AssistantAgent("assistant", model_client=model).run(
        task="Return a fixture greeting."
    )
    typed = await AssistantAgent(
        "typed", model_client=model, output_content_type=Answer
    ).run(task="Return a typed zero.")
    assert result.messages[-1].content == "Hello from AutoGen."
    assert typed.messages[-1].content.value == 0
    return "Text and typed zero verified."


if __name__ == "__main__":
    run("assistant-and-structured", scenario)
