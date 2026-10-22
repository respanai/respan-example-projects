"""Real provider-model streaming, event streaming and explicit early close."""

import asyncio
import inspect

from _fixtures import Fixture
from _shared import build_respan, example_scope
from agentscope.agent import Agent
from agentscope.message import UserMsg
from respan import workflow


async def main():
    fixture = Fixture()
    respan = build_respan("streaming", "agentscope_streaming")

    @workflow(name="agentscope_streaming")
    async def run(prompt):
        model = fixture.model(stream=True)
        source = await model([UserMsg(name="user", content=prompt)])
        assert inspect.isasyncgen(source)
        chunks = [chunk async for chunk in source]
        assert chunks[-1].content[0].text == "fixture stream"
        agent = Agent(name="StreamingAgent", system_prompt="Reply", model=model)
        events = [
            event
            async for event in agent.reply_stream(UserMsg(name="user", content=prompt))
        ]
        assert any(str(event.type).lower() == "reply_end" for event in events)
        source = await model([UserMsg(name="user", content="early close")])
        first = await anext(source)
        assert first.content[0].text == "fixture "
        await source.aclose()
        return {
            "final_text": "fixture stream",
            "early_close_text": first.content[0].text,
        }

    with example_scope("streaming"):
        try:
            print(await run("Stream a fixture response"))
        finally:
            try:
                await fixture.close()
            finally:
                respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
