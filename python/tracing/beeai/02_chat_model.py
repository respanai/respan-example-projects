"""Run a direct BeeAI ChatModel call with Respan tracing."""

import asyncio

from _shared import create_respan, example_attributes, get_chat_model
from respan import workflow

WORKFLOW_NAME = "BeeAI Chat Model Example"
respan = create_respan("beeai-chat-model")

from beeai_framework.backend import UserMessage


@workflow(name=WORKFLOW_NAME)
async def run_chat_model() -> str:
    model = get_chat_model()
    response = await model.run(
        [
            UserMessage(
                "Give two concise checks that make a traced AI workflow easier "
                "to debug."
            )
        ]
    )
    return response.get_text_content()


async def main() -> None:
    try:
        with example_attributes(WORKFLOW_NAME) as run_id:
            output = await run_chat_model()
            print(f"Run ID: {run_id}")
            print(f"Chat output: {output}")
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
