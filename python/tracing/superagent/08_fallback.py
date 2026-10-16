"""Released Superagent SDK scenario: fallback."""

import asyncio
from pathlib import Path

from _shared import client_context, create_respan, example_marker, finish_respan
from respan import propagate_attributes, workflow

SCRIPT_NAME = Path(__file__).name


@workflow(name=SCRIPT_NAME)
async def run_fallback(text: str):
    with client_context(retry=True) as client:
        result = await client.guard(
            input=text,
            model="openai/fixture-primary",
            fallback_model="openai/gpt-4o-mini",
        )
    assert result.classification == "pass"
    return {"classification": result.classification}


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
            result = await run_fallback("safe")
            print(result)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
