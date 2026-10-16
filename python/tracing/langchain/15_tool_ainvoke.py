"""Tool ainvoke."""

import asyncio

from _shared import init_telemetry, tracing_config
from langchain_core.tools import tool


@tool
async def async_add_numbers(left: int, right: int) -> int:
    """Add two integers asynchronously."""
    return left + right


async def tool_ainvoke() -> None:
    init_telemetry("langchain-tool-ainvoke")
    response = await async_add_numbers.ainvoke(
        {"left": 21, "right": 21},
        config=tracing_config("tool_ainvoke"),
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(tool_ainvoke())
