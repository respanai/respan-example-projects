from __future__ import annotations

import asyncio

from _shared import (
    example_attributes,
    finish_respan,
    first_message_text,
    make_async_client,
    make_custom_identifier,
    make_respan,
    model_name,
    print_result,
    print_start,
    workflow_name,
)
from respan import workflow

EXAMPLE_NAME = "async-chat"


@workflow(name=workflow_name(EXAMPLE_NAME))
async def _async_chat_workflow(prompt: str) -> str:
    async with make_async_client() as async_client:
        response = await async_client.chat.completions.create(
            model=model_name(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0,
        )
        return first_message_text(response)


async def run_async_chat() -> None:
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    respan = make_respan(EXAMPLE_NAME, custom_identifier)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print_start(EXAMPLE_NAME, custom_identifier)
            text = await _async_chat_workflow(
                "Reply with one concise sentence about async tracing."
            )
    finally:
        finish_respan(respan)

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    asyncio.run(run_async_chat())
