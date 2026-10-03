"""AgentScope tool/function call traced by Respan."""

from __future__ import annotations

import asyncio
from typing import ClassVar

from _shared import (
    ScriptedChatModel,
    build_respan,
    example_scope,
    text_response,
    tool_call_response,
)
from agentscope.agent import Agent
from agentscope.message import TextBlock, UserMsg
from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import ToolBase, ToolChunk, Toolkit


class WeatherTool(ToolBase):
    name = "lookup_weather"
    description = "Look up deterministic weather for a city."
    input_schema: ClassVar[dict] = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"},
        },
        "required": ["city"],
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(
            behavior=PermissionBehavior.ALLOW,
            message="Weather lookup is read-only.",
        )

    async def call(self, city: str) -> ToolChunk:
        return ToolChunk(content=[TextBlock(text=f"{city}: clear, 22C")])


async def main() -> None:
    model = ScriptedChatModel(
        model="agentscope-scripted-tools",
        responses=[
            tool_call_response(
                call_id="weather_call_1",
                name="lookup_weather",
                arguments={"city": "Tokyo"},
            ),
            text_response("Tokyo is clear and mild."),
        ],
    )
    respan = build_respan(
        example_name="tool-call",
        workflow_name="agentscope_tool_call",
        models=[model],
    )

    with example_scope("tool-call"):
        try:
            agent = Agent(
                name="WeatherAgent",
                system_prompt="Use tools when weather data is needed.",
                model=model,
                toolkit=Toolkit(tools=[WeatherTool()]),
            )

            result = await agent.reply(
                UserMsg(name="user", content="What is Tokyo weather?")
            )
            assert result.get_text_content() == "Tokyo is clear and mild."
            print(result.get_text_content())
        finally:
            respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
