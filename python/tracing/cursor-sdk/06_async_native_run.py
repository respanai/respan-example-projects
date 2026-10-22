import asyncio

from _fixtures import Fixture, events
from _shared import tracing
from cursor_sdk import SendOptions


async def run():
    with tracing("async-native-run") as (_, memory):
        values = []

        async def on_delta(value):
            values.append(value)

        fixture = Fixture(rows=events(tools=True))
        async with fixture.async_client() as client:
            agent = await fixture.agent(client)
            run = await agent.send("Fixture prompt", SendOptions(on_delta=on_delta))
            messages = [m async for m in run.stream()]
            assert messages and (await run.wait()).result == "Fixture completion"
        assert len(values) == 1 and len(memory.get_finished_spans()) == 2


if __name__ == "__main__":
    asyncio.run(run())
