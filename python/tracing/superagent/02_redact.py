"""Released Superagent SDK scenario: redact."""

import asyncio
from pathlib import Path

from _shared import client_context, create_respan, example_marker, finish_respan
from respan import propagate_attributes, workflow

SCRIPT_NAME = Path(__file__).name


@workflow(name=SCRIPT_NAME)
async def run_redact(text: str):
    from safety_agent.types import RedactOptions

    with client_context() as client:
        result = await client.redact(
            input=RedactOptions(
                input=text, model="openai/gpt-4o-mini", entities=["EMAIL"], rewrite=True
            )
        )
    assert result.redacted == "Contact <EMAIL_REDACTED>"
    return vars(result)


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
            result = await run_redact("Contact fixture-email@example.com")
            print(result)
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    asyncio.run(main())
