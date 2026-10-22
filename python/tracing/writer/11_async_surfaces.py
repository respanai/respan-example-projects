import asyncio

from _fixtures import NativeRuntime, invoke
from _shared import example_attributes, finish_respan, make_respan
from respan import workflow


@workflow(name="writer_async_surfaces")
async def scenario():
    runtime = NativeRuntime()
    async with runtime.async_client() as client:
        for operation in (
            "completion",
            "graph",
            "application",
            "vision",
            "translation",
            "web_search",
            "parse_pdf",
        ):
            await invoke(client, operation)
        for operation in ("chat", "completion", "graph", "application"):
            source = await invoke(client, operation, stream=True)
            assert len([chunk async for chunk in source]) == 300
            await source.close()
        source = await invoke(client, "chat", stream=True)
        await source.close()
    return "native async resources and four300chunk streams"


def run():
    respan = make_respan("async-surfaces")
    try:
        with example_attributes("async-surfaces"):
            print(asyncio.run(scenario()))
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run()
