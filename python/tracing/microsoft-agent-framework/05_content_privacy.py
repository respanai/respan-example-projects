"""Keep chat and tool content absent under Respan's scoped privacy setting."""

import asyncio

from _shared import (
    create_respan,
    create_streaming_fixture_client,
    finish_respan,
    workflow_attributes,
)
from agent_framework import Content, Message, tool
from opentelemetry import context
from respan import Respan, workflow
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY

WORKFLOW_NAME = "microsoft-agent-framework-content-privacy"


@tool
def echo(value: str) -> str:
    return value


@workflow(name=WORKFLOW_NAME)
async def run_example():
    client = create_streaming_fixture_client()
    await client.get_response(
        [Message("user", [Content.from_text("private MAF fixture prompt")])]
    )
    stream = client.get_response(
        [Message("user", [Content.from_text("private MAF stream prompt")])], stream=True
    )
    async for _ in stream:
        pass
    await echo.invoke(arguments={"value": "private MAF tool result"})
    return {"private_operations": 3}


async def main():
    respan = create_respan(WORKFLOW_NAME)
    token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
    try:
        with Respan.propagate_attributes(**workflow_attributes(WORKFLOW_NAME)):
            print(await run_example())
    finally:
        context.detach(token)
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
