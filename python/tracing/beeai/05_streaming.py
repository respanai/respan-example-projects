"""Iterate BeeAI's Run events and retain the SDK's final streamed result."""

import asyncio

from _shared import create_respan, example_attributes, get_chat_model
from respan import workflow

WORKFLOW_NAME = "BeeAI Streaming Example"
respan = create_respan("beeai-streaming")
from beeai_framework.backend import UserMessage


@workflow(name=WORKFLOW_NAME)
async def streaming():
    run = get_chat_model().run([UserMessage("Give two trace checks.")], stream=True)
    token_count = 0
    async for event, meta in run:
        if meta.name == "new_token":
            token_count += 1
    assert token_count > 0
    print(f"Observed token events: {token_count}")


async def main():
    try:
        with example_attributes(WORKFLOW_NAME):
            await streaming()
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
