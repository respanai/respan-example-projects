"""Room-free actual Session tools: preserve native spans, outputs and errorflags."""

import asyncio

from _shared import SCHEMA, FixtureLLM, Tracing, vector_tool
from livekit.agents import Agent, AgentSession, function_tool


@function_tool(raw_schema=SCHEMA)
async def failing_tool(raw_arguments: dict[str, object]):
    raise ValueError("controlled native session failure")


class OnceLLM(FixtureLLM):
    def chat(self, *, chat_ctx, tools=None, **kwargs):
        self.scenario = (
            "text"
            if any(item.type == "function_call_output" for item in chat_ctx.items)
            else "tools"
        )
        return super().chat(chat_ctx=chat_ctx, tools=tools, **kwargs)


async def main():
    tracing = Tracing("native-session")
    try:
        for tool in [vector_tool, failing_tool]:
            session = AgentSession(llm=OnceLLM())
            try:
                await session.start(
                    agent=Agent(
                        instructions="controlled room-free native fixture", tools=[tool]
                    )
                )
                await asyncio.wait_for(
                    session.run(user_input="controlled native tools"), 10
                )
            finally:
                await session.aclose()
        tools = [
            s
            for s in tracing.exporter.get_finished_spans()
            if s.name == "function_tool"
        ]
        assert len(tools) == 4 and all(
            s.attributes["respan.entity.log_type"] == "tool" for s in tools
        )
        assert sum(s.status.status_code.name == "ERROR" for s in tools) == 2
        print("two native tool outputs and two native errorflags; no room or cloud")
    finally:
        tracing.finish()


if __name__ == "__main__":
    asyncio.run(main())
