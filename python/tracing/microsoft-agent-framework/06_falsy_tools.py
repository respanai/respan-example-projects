"""Preserve false and zero tool results without losing the invocation span."""

import asyncio
import json

from _shared import (
    create_respan,
    create_streaming_fixture_client,
    finish_respan,
    workflow_attributes,
)
from agent_framework import Content, Message, tool
from respan import Respan, workflow

WORKFLOW_NAME = "microsoft-agent-framework-falsy-tools"


@tool
def is_available() -> bool:
    return False


@tool
def inventory_count() -> int:
    return 0


@workflow(name=WORKFLOW_NAME)
async def run_example():
    available = await is_available.invoke(arguments={})
    count = await inventory_count.invoke(arguments={})
    available = json.loads(available[0].text)
    count = json.loads(count[0].text)
    assert available is False and count == 0
    client = create_streaming_fixture_client()
    await client.get_response(
        [
            Message("user", [Content.from_text("Summarize the prior tool results")]),
            Message(
                "tool",
                [Content.from_function_result("available-call", result=available)],
            ),
            Message("tool", [Content.from_function_result("count-call", result=count)]),
        ]
    )
    return {"available": available, "count": count}


async def main():
    respan = create_respan(WORKFLOW_NAME)
    try:
        with Respan.propagate_attributes(**workflow_attributes(WORKFLOW_NAME)):
            print(await run_example())
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
