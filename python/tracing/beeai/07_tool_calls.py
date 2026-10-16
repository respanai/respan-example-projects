"""Connect a model-produced call ID to the SDK tool run and result message."""

import asyncio
import json

from _shared import create_respan, example_attributes, get_chat_model
from respan import workflow

WORKFLOW_NAME = "BeeAI Tool Calls Example"
respan = create_respan("beeai-tool-calls")
from beeai_framework.backend import (
    MessageToolResultContent,
    ToolMessage,
    UserMessage,
)
from beeai_framework.tools import tool


@tool(name="city_summary", description="Return a deterministic city summary.")
def city_summary(city: str) -> str:
    return f"{city}: a fixture city summary."


@workflow(name=WORKFLOW_NAME)
async def tool_calls():
    response = await get_chat_model(mode="tool").run(
        [UserMessage("Summarize Paris with city_summary.")], tools=[city_summary]
    )
    results = []
    for call in response.get_tool_calls():
        output = await city_summary.run(json.loads(call.args)).context(
            {"tool_call_msg": call}
        )
        results.append(
            ToolMessage(
                MessageToolResultContent(
                    tool_call_id=call.id,
                    tool_name=call.tool_name,
                    result=output.get_text_content(),
                )
            )
        )
    final = await get_chat_model().run(
        [UserMessage("Use the tool result."), *response.output, *results]
    )
    print(final.get_text_content())


async def main():
    try:
        with example_attributes(WORKFLOW_NAME):
            await tool_calls()
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
