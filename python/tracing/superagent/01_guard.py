"""Released Superagent SDK scenario: guard."""

import asyncio
from pathlib import Path

from _shared import client_context, create_respan, example_marker, finish_respan
from respan import propagate_attributes, workflow

SCRIPT_NAME = Path(__file__).name


@workflow(name=SCRIPT_NAME)
async def run_guard(text: str):
    with client_context() as client:
        result = await client.guard(
            input=text,
            model="openai/gpt-4o-mini",
            chunk_size=6,
            system_prompt="fixture guard instructions",
        )
    assert result.classification == "block" and result.usage.prompt_tokens == 0
    return {"classification": result.classification, "usage": vars(result.usage)}


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
            result = await run_guard("safe block safe")
            print(result)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
