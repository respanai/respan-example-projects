"""Native async workflow/task/tool hierarchy preserves awaited values."""

import asyncio

from _shared import build_respan
from agentops import task, tool, trace


def main():
    telemetry = build_respan(example_name="async", workflow_name="agentops_async")

    @task(name="prepare_async")
    async def prepare(value):
        return value.upper()

    @tool(name="lookup_async")
    async def lookup(value):
        return {"actual": value}

    @trace(name="async_workflow")
    async def run():
        return await lookup(await prepare("controlled"))

    try:
        assert asyncio.run(run()) == {"actual": "CONTROLLED"}
    finally:
        telemetry.shutdown()


if __name__ == "__main__":
    main()
