"""Trace a controlled model failure; live mode uses a rejected provider request."""

import asyncio

from _shared import create_respan, example_attributes, get_chat_model
from respan import workflow

WORKFLOW_NAME = "BeeAI Expected Error Example"
respan = create_respan("beeai-expected-error")

from beeai_framework.backend import UserMessage
from beeai_framework.errors import FrameworkError


@workflow(name=WORKFLOW_NAME)
async def run_expected_error() -> None:
    model = get_chat_model(error=True)
    await model.run([UserMessage("This request should fail before completion.")])


async def main() -> None:
    try:
        with example_attributes(WORKFLOW_NAME) as run_id:
            try:
                await run_expected_error()
            except FrameworkError as exc:
                print(f"Run ID: {run_id}")
                print(f"Observed expected error: {type(exc).__name__}")
            else:
                raise AssertionError("The invalid BeeAI model unexpectedly succeeded")
    finally:
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
