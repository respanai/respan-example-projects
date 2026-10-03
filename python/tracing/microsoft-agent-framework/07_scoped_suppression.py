"""Honor OTel suppression while keeping operations outside the scope visible."""

import asyncio

from _shared import (
    create_respan,
    create_streaming_fixture_client,
    finish_respan,
    workflow_attributes,
)
from agent_framework import Content, Message
from opentelemetry.instrumentation.utils import suppress_instrumentation
from respan import Respan, workflow

WORKFLOW_NAME = "microsoft-agent-framework-scoped-suppression"


@workflow(name=WORKFLOW_NAME)
async def run_example():
    client = create_streaming_fixture_client()
    await client.get_response(
        [Message("user", [Content.from_text("Visible before suppression")])]
    )
    with suppress_instrumentation():
        await client.get_response(
            [
                Message(
                    "user",
                    [Content.from_text("Suppressed fixture must not be exported")],
                )
            ]
        )
    await client.get_response(
        [Message("user", [Content.from_text("Visible after suppression")])]
    )
    return {"visible_calls": 2, "suppressed_calls": 1}


async def main():
    respan = create_respan(WORKFLOW_NAME)
    try:
        with Respan.propagate_attributes(**workflow_attributes(WORKFLOW_NAME)):
            print(await run_example())
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
