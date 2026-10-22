"""Released Superagent SDK scenario: input_types."""

import asyncio
from pathlib import Path

from _shared import client_context, create_respan, example_marker, finish_respan
from respan import propagate_attributes, workflow

SCRIPT_NAME = Path(__file__).name


@workflow(name=SCRIPT_NAME)
async def run_input_types(url: str):
    with client_context() as client:
        image = await client.guard(
            input=b"\x89PNG\r\n\x1a\nfixture image", model="openai/gpt-4o-mini"
        )
        remote = await client.guard(input=url, model="openai/gpt-4o-mini")
    assert image.classification == remote.classification == "pass"
    return {"bytes": "pass", "url": "pass"}


async def main():
    respan = create_respan(SCRIPT_NAME)
    marker = example_marker()
    try:
        with propagate_attributes(
            trace_group_identifier=SCRIPT_NAME,
            thread_identifier=marker + "-thread",
            metadata={
                "run_id": marker,
                "integration": "superagent",
                "example": SCRIPT_NAME,
            },
        ):
            result = await run_input_types("https://example.com/fixture.txt")
            print(result)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
