"""Released Superagent SDK scenario: expected_error."""

import asyncio
from pathlib import Path

from _shared import client_context, create_respan, example_marker, finish_respan
from respan import propagate_attributes, workflow

SCRIPT_NAME = Path(__file__).name


@workflow(name=SCRIPT_NAME)
async def run_failures(text: str):
    with client_context(fail=True) as client:
        try:
            await client.guard(input=text, model="openai/gpt-4o-mini")
        except RuntimeError as error:
            assert "401" in str(error)
        else:
            raise AssertionError("Expected controlled HTTP401")
        try:
            await client.guard(input=text, model="openai/gpt-4o-mini", chunk_size=-1)
        except ValueError:
            pass
        else:
            raise AssertionError("Expected native validation error")
    return {"controlled_failures": 2}


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
            result = await run_failures("controlled failure")
            print(result)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
